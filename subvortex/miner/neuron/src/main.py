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

from subvortex.core.protocol import Score
from subvortex.core.shared.neuron import wait_until_registered
from subvortex.core.shared.substrate import (
    get_weights_min_stake_async,
    get_owner_hotkey,
)
from subvortex.core.shared.mock import MockSubtensor, MockAxon
from subvortex.core.version import get_version

from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.metagraph import SubVortexMetagraph
from subvortex.core.core_bittensor.axon import SubVortexAxon
from subvortex.core.core_bittensor.synapse import Synapse
from subvortex.core.model.neuron.neuron import Neuron
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

# An asyncio event to signal when shutdown is complete
shutdown_complete = asyncio.Event()


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

        self.loop = asyncio.get_running_loop()

        await self._initialize()
        await self._serve()
        await self._main_loop()

        # Signal the neuron has finished
        self.run_complete.set()

    async def shutdown(self):
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

    async def _initialize(self):
        self.wallet = (
            btwm.MockWallet(config=self.config)
            if self.config.mock
            else btw.Wallet(config=self.config)
        )
        self.wallet.create_if_non_existent()
        btul.logging.info(f"Wallet initialized: {self.wallet}")

        network = "finney" if self.settings.dry_run else "local"
        self.subtensor = (
            MockSubtensor(self.config.netuid, wallet=self.wallet)
            if self.config.miner.mock_subtensor
            else btcas.AsyncSubtensor(
                config=self.config, network=network, retry_forever=True
            )
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
        self.neuron = self.neurons.get(
            self.wallet.hotkey.ss58_address, Neuron.create_empty()
        )
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
                blacklist_fn=self._sync_blacklist_handler,
            )
            if self.config.mock
            else SubVortexAxon(
                wallet=self.wallet,
                config=self.config,
                external_ip=btun.get_external_ip(),
                blacklist_fn=self._sync_blacklist_handler,
            )
        )
        self.axon.attach(
            forward_fn=self._score,
            blacklist_fn=self._sync_blacklist_score_handler,
        )

        if not self.settings.dry_run:
            # Start the axon
            await self.subtensor.serve_axon(netuid=self.config.netuid, axon=self.axon)
            self.axon.start()

        # Update the firewall if enable
        if self.firewall:
            await self._update_firewall()

    async def _main_loop(self):
        while not self.should_exit.is_set():
            try:
                # Wait for either a new block OR a shutdown signal, whichever comes first.
                done, _ = await asyncio.wait(
                    [
                        self.subtensor.wait_for_block(),
                        self.should_exit.wait(),
                    ],
                    timeout=24,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Timeout, no tasks completed
                if not done:
                    btul.logging.warning(
                        "⏲️ No new block retrieved within 24 seconds. Retrying..."
                    )
                    continue

                # If shutdown signal is received, break the loop immediately
                if self.should_exit.is_set():
                    break

                # If no new block was produced (e.g., shutdown happened or something failed), skip this round
                # This guards against the case where wait_for_block() returned None or False
                if not any(task.result() for task in done if not task.cancelled()):
                    continue

                # Get the current block
                current_block = await self.subtensor.get_current_block()
                btul.logging.debug(f"📦 Block #{current_block}")

                # Ensure the metagraph is ready
                btul.logging.debug("Ensure metagraph readiness")
                await self.database.wait_until_ready("metagraph")

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
                    self.neuron = self.neurons.get(
                        self.wallet.hotkey.ss58_address, Neuron.create_empty()
                    )
                    btul.logging.info(
                        f"Local miner neuron: {self.neuron.hotkey} (UID: {self.neuron.uid}, IP: {self.neuron.ip})"
                    )

                    if not self.settings.dry_run:
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

                # Get the next block
                current_block = await self.subtensor.get_current_block()

                # Ensure the subvortex metagraph has been synced within its mandatory interval
                # We add a buffer of 5 minutes to ensure metagraph has time to sync
                assert last_updated >= (
                    current_block - (self.settings.metagraph_sync_interval + 25)
                ), (
                    f"⚠️ Metagraph may be out of sync! Last update was at block {last_updated}, "
                    f"but current block is {current_block}. Ensure your metagraph is syncing properly."
                )

            except AssertionError:
                # We already display a log, so need to do more here
                pass

            except ConnectionRefusedError as e:
                btul.logging.error(f"Connection refused: {e}")
                await asyncio.sleep(1)

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

    async def _blacklist(self, synapse: Synapse) -> typing.Tuple[bool, str]:
        caller = synapse.dendrite.hotkey
        caller_version = synapse.dendrite.neuron_version or 0
        synapse_type = type(synapse).__name__

        # Whitelist the subnet owner hotkey
        owner_hotkey = get_owner_hotkey(self.subtensor.substrate, self.config.netuid)
        if caller == owner_hotkey:
            return False, "Hotkey recognized!"

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

        # Display reason
        if synapse.reason and synapse.reason.strip():
            detail = synapse.detail.strip() if synapse.detail else ""
            btul.logging.debug(
                f"[{validator_uid}] Reason: {synapse.reason.strip()}, Detail: {detail}"
            )

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

    def _sync_blacklist_handler(self, synapse: Synapse) -> typing.Tuple[bool, str]:
        result = self._run_safe(self._blacklist(synapse))
        return result or (True, "Error during blacklist check")

    def _sync_blacklist_score_handler(self, synapse: Score) -> typing.Tuple[bool, str]:
        result = self._run_safe(self._blacklist(synapse))
        return result or (True, "Error during blacklist check")

    def _run_safe(self, coro: typing.Coroutine, timeout: float = 10):
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)
            return future.result(timeout=timeout)

        except ConnectionRefusedError as e:
            pass

        except Exception as e:
            btul.logging.error(f"Error in threaded Axon handler: {e}")
            btul.logging.debug(traceback.format_exc())
            return None


async def main():
    # Initialize miner
    miner = Miner()

    # Get the current asyncio event loop
    loop = asyncio.get_running_loop()

    # Define a signal handler that schedules the shutdown coroutine
    def _signal_handler():
        # Schedule graceful shutdown without blocking the signal handler
        loop.create_task(_shutdown(miner))

    # Register signal handlers for SIGINT (Ctrl+C) and SIGTERM (kill command)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    # Start the main service logic
    await miner.run()

    # Block here until shutdown is signaled and completed
    await shutdown_complete.wait()


async def _shutdown(miner: Miner):
    # Gracefully shut down the service
    await miner.shutdown()

    # Notify the main function that shutdown is complete
    shutdown_complete.set()


if __name__ == "__main__":
    try:
        # Start the main asyncio loop
        asyncio.run(main())

    except Exception as e:
        # Log any unexpected exceptions that bubble up
        btul.logging.error(f"Unhandled exception: {e}")
        btul.logging.debug(traceback.format_exc())
