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
import time
import typing
import asyncio
import threading
import traceback
import websockets
import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul
import bittensor.utils.networking as btun
import bittensor_wallet.wallet as btw
import bittensor_wallet.mock as btwm
from dotenv import load_dotenv

from subvortex.core.protocol import Score
from subvortex.core.shared.neuron import wait_until_registered
from subvortex.core.shared.substrate import get_weights_min_stake_async
from subvortex.core.shared.mock import MockSubtensor, MockAxon
from subvortex.core.version import get_version

from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.metagraph import SubVortexMetagraph
from subvortex.core.core_bittensor.axon import SubVortexAxon
from subvortex.core.core_bittensor.synapse import Synapse
from subvortex.core.core_bittensor.subtensor import wait_for_block

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

        # Init the event loop.
        self.loop = asyncio.get_event_loop()

        # Instantiate runners
        self.should_exit: bool = False
        self.is_running: bool = False
        self.thread: threading.Thread = None
        self.lock = asyncio.Lock()
        self.request_timestamps: typing.Dict = {}
        self.previous_last_updates = []
        self.previous_last_updated = None
        self.block_queue = asyncio.Queue()

        self.step = 0

        self.request_log = load_request_log(self.config.miner.request_log_path)

    async def run(self):
        try:
            # Display the settings
            btul.logging.info(f"Settings: {self.settings}")

            # Show miner version
            self.version = get_version("subvortex-miner-neuron")
            btul.logging.debug(f"Version: {self.version}")

            await self._initialize()
            await self._serve()
            await self._main_loop()
        except KeyboardInterrupt:
            btul.logging.info("Keyboard interrupt detected, exiting.")
        finally:
            await self._shutdown()

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
            else btcas.AsyncSubtensor(config=self.config, network="local")
        )
        await self._retry_initialize_subtensor()

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
        must_init_subtensor = False
        while not self.should_exit:
            try:
                # Re-initialize the subtensor if needed
                if must_init_subtensor:
                    btul.logging.warning(
                        "Reinitializing subtensor due to previous failure..."
                    )
                    await self._retry_initialize_subtensor()
                    must_init_subtensor = False

                # Wait for the next block
                result = await wait_for_block(subtensor=self.subtensor)
                if not result:
                    continue

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

            except (
                BrokenPipeError,
                ConnectionError,
                TimeoutError,
                websockets.exceptions.ConnectionClosedError,
            ) as e:
                btul.logging.error(f"Connection issue in main loop: {e}")
                btul.logging.debug(traceback.format_exc())
                must_init_subtensor = True
                await asyncio.sleep(5)

            except Exception as ex:
                btul.logging.error(f"Unhandled exception in main loop: {ex}")
                btul.logging.debug(traceback.format_exc())
                await asyncio.sleep(5)

    async def _retry_initialize_subtensor(self, max_attempts: int = 5):
        backoff = 2
        for attempt in range(max_attempts):
            try:
                btul.logging.info(f"Initializing subtensor (attempt {attempt + 1})...")
                await self.subtensor.initialize()
                btul.logging.success("Subtensor initialized.")
                return
            except Exception as e:
                btul.logging.error(f"Subtensor init failed: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

        raise RuntimeError("Failed to initialize subtensor after retries.")

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
        btul.logging.info("Shutting down miner services...")
        self.sse and self.sse.stop()
        self.firewall and self.firewall.stop()
        self.file_monitor and self.file_monitor.stop()
        self.axon and self.axon.stop()

        if not self.loop.is_closed():
            await self.loop.shutdown_asyncgens()
            self.loop.close()

        if hasattr(self, "subtensor"):
            await self.subtensor.close()

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

        if synapse.count > 1:
            btul.logging.error(
                f"[{validator_uid}] {synapse.count} miners are running on this machine"
            )

        btul.logging.info(
            f"[{validator_uid}] Availability score {synapse.availability}"
        )
        btul.logging.info(f"[{validator_uid}] Latency score {synapse.latency}")
        btul.logging.info(f"[{validator_uid}] Reliability score {synapse.reliability}")
        btul.logging.info(
            f"[{validator_uid}] Distribution score {synapse.distribution}"
        )
        btul.logging.success(f"[{validator_uid}] Score {synapse.score}")

        synapse.version = self.version

        return synapse

    async def _blacklist_score(self, synapse: Score) -> typing.Tuple[bool, str]:
        return await self._blacklist(synapse)


if __name__ == "__main__":
    asyncio.run(Miner().run())
