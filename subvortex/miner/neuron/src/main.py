# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import typing
import signal
import asyncio
import traceback
import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul
import bittensor.utils.networking as btun
import bittensor_wallet.wallet as btw
import bittensor_wallet.mock as btwm
from dotenv import load_dotenv

import bittensor.core.settings as btcs
import bittensor_wallet.utils as btwu

from subvortex.core.protocol import Score
from subvortex.core.shared.neuron import wait_until_registered
from subvortex.core.shared.substrate import get_weights_min_stake_async
from subvortex.core.shared.mock import MockSubtensor, MockAxon
from subvortex.core.version import get_version

from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.metagraph import SubVortexMetagraph
from subvortex.core.core_bittensor.axon import SubVortexAxon
from subvortex.core.core_bittensor.synapse import Synapse
from subvortex.core.core_bittensor.subtensor import wait_for_block, RetryAsyncSubstrate

from subvortex.core.sse.sse_thread import SSEThread

from subvortex.core.file.file_monitor import FileMonitor
from subvortex.core.firewall.firewall_factory import (
    create_firewall_tool,
    create_firewall_observer,
)
from subvortex.miner.neuron.src.firewall import Firewall
from subvortex.miner.neuron.src.config import (
    config,
    check_config,
    add_args,
)
from subvortex.miner.neuron.src.utils import load_request_log
from subvortex.miner.neuron.src.settings import Settings
from subvortex.miner.neuron.src.database import Database
from subvortex.miner.neuron.src.neuron import (
    wait_until_no_multiple_occurrences,
    get_validators,
)

# Load the environment variables for the whole process
load_dotenv(override=True)


class Miner:
    @classmethod
    def check_config(cls, config: "btcc.Config"):
        """
        Adds neuron-specific arguments to the argument parser.

        Args:
            parser (argparse.ArgumentParser): Parser to add arguments to.

        This class method enriches the argument parser with options specific to the neuron's configuration.
        """
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        """
        Adds neuron-specific arguments to the argument parser.

        Args:
            parser (argparse.ArgumentParser): Parser to add arguments to.

        This class method enriches the argument parser with options specific to the neuron's configuration.
        """
        add_args(cls, parser)

    @classmethod
    def config(cls):
        """
        Retrieves the configuration for the neuron.

        Returns:
            btcc.Config: The configuration object for the neuron.

        This class method returns the neuron's configuration, which is used throughout the neuron's lifecycle
        for various functionalities and operations.
        """
        return config(cls)

    subtensor: "btcas.AsyncSubtensor"
    wallet: "btw.Wallet"
    metagraph: SubVortexMetagraph

    def __init__(self):
        self.config, parser = Miner.config()
        self.check_config(self.config)

        # Create settings
        self.settings = Settings.create()
        update_config(self.settings, self.config, parser)

        btul.logging(
            config=self.config,
            logging_dir=self.config.miner.full_path,
            debug=True,
        )
        btul.logging.set_trace(self.config.logging.trace)
        btul.logging._stream_formatter.set_trace(self.config.logging.trace)
        btul.logging.info(str(self.config))

        # Instantiate runners
        self.previous_last_updated = None
        self.should_exit = asyncio.Event()
        self.run_complete = asyncio.Event()

        self.step = 0

        self.request_log = load_request_log(self.config.miner.request_log_path)

    async def run(self):
        # Display the settings
        btul.logging.info(f"Settings: {self.settings}")

        # Show miner version
        self.version = get_version()
        btul.logging.debug(f"Version: {self.version}")

        await self._initialize()
        await self._serve()
        await self._main_loop()

        # Signal the neuron has finished
        self.run_complete.set()

    async def _initialize(self):
        self.wallet = (
            btwm.MockWallet(config=self.config)
            if self.config.mock
            else btw.Wallet(config=self.config)
        )
        self.wallet.create_if_non_existent()
        btul.logging.info(f"Wallet initialized: {self.wallet}")

        self.subtensor = (
            MockSubtensor(self.config.netuid, wallet=self.wallet)
            if self.config.miner.mock_subtensor
            else btcas.AsyncSubtensor(
                config=self.config, network="local", retry_forever=True
            )
        )
        # TODO: remove once OTF patched it
        self.subtensor.substrate = RetryAsyncSubstrate(
            url=self.subtensor.chain_endpoint,
            ss58_format=btwu.SS58_FORMAT,
            type_registry=btcs.TYPE_REGISTRY,
            retry_forever=True,
            use_remote_preset=True,
            chain_name="Bittensor",
            _mock=False,
        )
        await self.subtensor.initialize()

        # Initialize database
        btul.logging.info("Waiting for database readiness...")
        self.database = Database(settings=self.settings)
        await self.database.wait_until_ready("metagraph")
        btul.logging.info("Database is ready.")

        # Get the list of neurons
        self.neurons = await self.database.get_neurons()
        btul.logging.info(f"Loaded {len(self.neurons)} neurons from the database.")

        # Get the miner
        self.neuron = self.neurons[self.wallet.hotkey.ss58_address]
        btul.logging.info(
            f"Neuron details — Hotkey: {self.neuron.hotkey}, UID: {self.neuron.uid}, IP: {self.neuron.ip}"
        )

        btul.logging.success("Initialization complete.")

    async def _serve(self):
        # Initialise the file monitor
        self.file_monitor = FileMonitor()
        self.file_monitor.start()

        # Initialize the SSE
        self.sse = SSEThread(ip=self.config.sse.firewall.ip, port=self.config.sse.port)
        self.sse.server.add_stream("firewall")
        self.sse.start()

        # Initialize firewall if enabled
        self.firewall = None
        if self.config.firewall.on:
            btul.logging.debug("Starting firewall...")
            self.firewall = Firewall(
                observer=create_firewall_observer(),
                tool=create_firewall_tool(),
                sse=self.sse.server,
                port=self.config.axon.external_port or self.config.axon.port,
                interface=self.config.firewall.interface,
                config_file=self.config.firewall.config,
            )
            self.file_monitor.add_file_provider(self.firewall.provider)
            self.firewall.start()

        # Initialize the axon
        self.axon = (
            MockAxon(
                wallet=self.wallet,
                config=self.config,
                external_ip=btun.get_external_ip(),
                blacklist_fn=self._blacklist,
            )
            if self.config.mock
            else SubVortexAxon(
                wallet=self.wallet,
                config=self.config,
                external_ip=btun.get_external_ip(),
                blacklist_fn=self._blacklist,
            )
        )
        self.axon.attach(forward_fn=self._score, blacklist_fn=self._blacklist_score)

        # Start the axon
        await self.subtensor.serve_axon(netuid=self.config.netuid, axon=self.axon)
        self.axon.start()

        # Update the firewall if enable
        if self.firewall:
            await self._update_firewall()

    async def _main_loop(self):
        while not self.should_exit.is_set():
            try:
                # Wait for the next block
                if not await wait_for_block(subtensor=self.subtensor):
                    continue

                self.subtensor.wait_for_block

                # Get the current block
                current_block = await self.subtensor.get_current_block()
                btul.logging.debug(f"Block #{current_block}")

                # Get the last time the neurons have been updated
                last_updated = await self.database.get_neuron_last_updated()
                if self.previous_last_updated != last_updated:
                    btul.logging.debug(
                        f"Neurons have changed at block #{current_block}"
                    )

                    # Neurons have changed
                    self.previous_last_updated = last_updated

                    # Get the list of neurons
                    self.neurons = await self.database.get_neurons()
                    btul.logging.debug(
                        f"Loaded {len(self.neurons)} neurons from the database."
                    )

                    # Get the miner
                    self.neuron = self.neurons[self.wallet.hotkey.ss58_address]
                    btul.logging.info(
                        f"Local miner neuron: {self.neuron.hotkey} (UID: {self.neuron.uid}, IP: {self.neuron.ip})"
                    )

                    # Wait until there is only one neuron for the current ip
                    # Ensure we have only one ip per miner
                    await wait_until_no_multiple_occurrences(
                        self.database, self.neuron.ip
                    )

                    # Wait until the miner is registered
                    # Ensure the miner is registered
                    await wait_until_registered(
                        self.database, self.wallet.hotkey.ss58_address
                    )

                    # Update the firewall is enabled
                    self.firewall and await self._update_firewall()

            except Exception as ex:
                btul.logging.error(f"Unhandled exception in main loop: {ex}")
                btul.logging.debug(traceback.format_exc())

    async def _update_firewall(self):
        # Get version and min stake
        version = await self.subtensor.get_hyperparameter(
            "weights_version", netuid=self.settings.uid
        )

        # Get the min stake to set weight
        weights_min_stake = await get_weights_min_stake_async(self.subtensor.substrate)

        # Update the specifications
        specifications = {
            "neuron_version": version,
            "synapses": self.axon.forward_class_types,
            "hotkey": self.wallet.hotkey.ss58_address,
        }
        btul.logging.debug(f"Firewall specifications {specifications}")

        # Define the valid validators
        validators = get_validators(
            neurons=self.neurons.values(), weights_min_stake=weights_min_stake
        )
        valid_validators = [x.hotkey for x in validators]

        # Update the firewall
        self.firewall.update(
            specifications=specifications,
            whitelist_hotkeys=valid_validators,
        )
        btul.logging.debug("Firewall updated")

    async def _shutdown(self):
        btul.logging.info("Shutting down miner...")

        # Notify the miner to stop
        self.should_exit.set()

        # Wait the neuron to stop
        await self.run_complete.wait()

        if getattr(self, "axon", None):
            self.axon.stop()
            btul.logging.debug("Axon stopped")

        if getattr(self, "subtensor", None):
            await self.subtensor.close()
            btul.logging.debug("Subtensor stopped")

        if getattr(self, "sse", None):
            self.sse.stop()

        if getattr(self, "firewall", None):
            self.firewall.stop()

        if getattr(self, "file_monitor", None):
            self.file_monitor.stop()

        btul.logging.info("Shutting down miner completed")

    async def _blacklist(self, synapse: Synapse) -> typing.Tuple[bool, str]:
        caller = synapse.dendrite.hotkey
        caller_version = synapse.dendrite.neuron_version or 0
        synapse_type = type(synapse).__name__

        # Get the list of all validators
        validators = get_validators(neurons=self.neurons.values())

        # Get the validator associated to the hotkey
        validator = next((x for x in validators if x.hotkey == caller), None)

        # Block hotkeys that are not an active validator hotkey
        if not validator:
            btul.logging.debug(
                f"Blacklisted a {synapse_type} request from a unrecognized hotkey {caller}"
            )
            return True, "Unrecognized hotkey"

        # Block hotkeys that do not have the latest version
        hyperparameters = await self.subtensor.get_subnet_hyperparameters(
            self.config.netuid
        )
        if caller_version < hyperparameters.weights_version:
            btul.logging.debug(
                f"Blacklisted a {synapse_type} request from a non-updated hotkey {caller}"
            )
            return True, "Non-updated hotkey"

        # Block hotkeys that do not have the minimum require stake to set weight
        weights_min_stake = await get_weights_min_stake_async(self.subtensor.substrate)
        if validator.stake < weights_min_stake:
            btul.logging.debug(
                f"Blacklisted a {synapse_type} request from a not enought stake hotkey {caller}"
            )
            return True, "Not enough stake hotkey"

        btul.logging.trace(f"Not Blacklisting recognized hotkey {caller}")
        return False, "Hotkey recognized!"

    def _score(self, synapse: Score) -> Score:
        validator_uid = synapse.validator_uid

        # Display the block of the challenge
        btul.logging.info(f"[{validator_uid}] Challenge at block #{synapse.block}")

        # Display error if there are more than 1 miner running on this machine
        if synapse.count > 1:
            btul.logging.error(
                f"[{validator_uid}] {synapse.count} miners are running on this machine"
            )

        # Display the penalty factor
        if synapse.penalty_factor:
            btul.logging.warning(
                f"[{validator_uid}] Penalty factor {synapse.penalty_factor}"
            )
        else:
            btul.logging.debug(f"[{validator_uid}] No penalty factor")

        # Display scores
        btul.logging.debug(
            f"[{validator_uid}] Availability score {synapse.availability}"
        )
        btul.logging.debug(f"[{validator_uid}] Latency score {synapse.latency}")
        btul.logging.debug(f"[{validator_uid}] Reliability score {synapse.reliability}")
        btul.logging.debug(
            f"[{validator_uid}] Distribution score {synapse.distribution}"
        )
        btul.logging.info(f"[{validator_uid}] Score {synapse.score}")
        btul.logging.info(f"[{validator_uid}] Moving score {synapse.moving_score}")
        btul.logging.success(f"[{validator_uid}] Rank {synapse.rank}")

        # Update the version
        synapse.version = self.version

        return synapse

    async def _blacklist_score(self, synapse: Score) -> typing.Tuple[bool, str]:
        return await self._blacklist(synapse)


if __name__ == "__main__":
    miner = Miner()

    def _handle_signal(sig, frame):
        loop.call_soon_threadsafe(lambda: asyncio.create_task(miner._shutdown()))

    # Create and set a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Register signal handlers (in main thread)
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        # Run the miner
        loop.run_until_complete(miner.run())

    except Exception as e:
        btul.logging.error(f"Unhandled exception: {e}")
        btul.logging.debug(traceback.format_exc())
    finally:
        # Cleanup async generators and close loop
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
