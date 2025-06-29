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
import signal
import asyncio
import traceback
import numpy as np
import bittensor.core.config as btcc
import bittensor.core.subtensor as btcs
import bittensor.core.metagraph as btcm
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw
import bittensor_wallet.mock as btwm
from typing import List
from dotenv import load_dotenv

from subvortex.core.monitor.monitor import Monitor
from subvortex.core.country.country_service import CountryService
from subvortex.core.file.file_monitor import FileMonitor
from subvortex.core.shared.neuron import wait_until_registered
from subvortex.core.shared.mock import MockDendrite, MockSubtensor
from subvortex.core.shared.substrate import get_weights_min_stake
from subvortex.core.model.neuron.neuron import Neuron
from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.dendrite import SubVortexDendrite, close_dendrite
from subvortex.core.core_bittensor.subtensor import (
    get_number_of_uids,
    get_next_block,
    get_number_of_uids,
)
from subvortex.core.version import to_spec_version, get_version

from subvortex.validator.neuron.src.config import config, check_config, add_args
from subvortex.validator.neuron.src.checks import check_redis_connection
from subvortex.validator.neuron.src.forward import forward
from subvortex.validator.neuron.src.models.miner import Miner
from subvortex.validator.neuron.src.state import (
    load_state,
    save_state,
    init_wandb,
    finish_wandb,
    should_reinit_wandb,
    log_event,
)
from subvortex.validator.neuron.src.weights import (
    set_weights,
)
from subvortex.validator.neuron.src.settings import Settings
from subvortex.validator.neuron.src.database import Database
from subvortex.validator.neuron.src.miner import sync_miners
from subvortex.validator.neuron.src.weights import should_set_weights


# Load the environment variables for the whole process
load_dotenv(override=True)

# An asyncio event to signal when shutdown is complete
shutdown_complete = asyncio.Event()


class Validator:
    """
    A Neuron instance represents a node in the Bittensor network that performs validation tasks.
    It manages the data validation cycle, including storing, challenging, and retrieving data,
    while also participating in the network consensus.

    Attributes:
        subtensor (bt_subtensor.Subtensor): The interface to the Bittensor network's blockchain.
        wallet (btw.wallet): Cryptographic wallet containing keys for transactions and encryption.
        metagraph (btcm.metagraph): Graph structure storing the state of the network.
        database (redis.StrictRedis): Database instance for storing metadata and proofs.
        moving_averaged_scores: Tensor tracking performance scores of other nodes.
    """

    @classmethod
    def check_config(cls, config: "btcc.Config"):
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        add_args(cls, parser)

    @classmethod
    def config(cls):
        return config(cls)

    subtensor: "btcs.Subtensor"
    wallet: "btw.Wallet"
    metagraph: "btcm.Metagraph"

    def __init__(self):
        self.config, parser = Validator.config()
        self.check_config(self.config)

        # Create settings
        self.settings = Settings.create()
        update_config(self.settings, self.config, parser)

        btul.logging(
            config=self.config,
            logging_dir=self.config.neuron.full_path,
            debug=True,
        )
        btul.logging.set_trace(self.config.logging.trace)
        btul.logging._stream_formatter.set_trace(self.config.logging.trace)
        btul.logging.debug(str(self.config))

        # Instantiate runners
        self.step = 0
        self.miners: List[Miner] = []
        self.should_exit = asyncio.Event()
        self.run_complete = asyncio.Event()

    async def run(self):
        # Display the settings
        btul.logging.info(f"Settings: {self.settings}")

        # Show miner version
        version = get_version()
        btul.logging.debug(f"Version: {version}")

        # Init validator wallet.
        btul.logging.debug(f"loading wallet")
        self.wallet = (
            btwm.get_mock_wallet()
            if self.config.mock
            else btw.Wallet(config=self.config)
        )
        self.wallet.create_if_non_existent()
        btul.logging.debug(f"wallet: {str(self.wallet)}")

        # Init subtensor
        btul.logging.debug("loading subtensor")
        self.subtensor = (
            MockSubtensor(self.config.netuid, wallet=self.wallet)
            if self.config.mock
            else btcs.Subtensor(config=self.config)
        )
        btul.logging.debug(str(self.subtensor))

        # Initialize the database
        btul.logging.info("loading database")
        self.database = Database(settings=self.settings)

        # Get the numbers of neuron
        self.number_of_uids = get_number_of_uids(
            subtensor=self.subtensor, netuid=self.settings.netuid
        )
        btul.logging.debug(f"# of neurons: {self.number_of_uids}")

        # Dendrite pool for querying the network.
        btul.logging.debug("loading dendrite_pool")
        if self.config.neuron.mock_dendrite_pool:
            self.dendrite = MockDendrite(wallet=self.wallet)
        else:
            self.dendrite = SubVortexDendrite(
                version=to_spec_version(version), wallet=self.wallet
            )
        btul.logging.debug(str(self.dendrite))

        # Check if the connection to the database is successful
        await check_redis_connection(port=self.settings.database_port)

        # Wait until the metagraph is ready
        await self.database.wait_until_ready("metagraph")

        # File monitor
        self.file_monitor = FileMonitor()
        self.file_monitor.start()

        # Monitor miners
        self.monitor = Monitor(self.config.netuid)
        self.file_monitor.add_file_provider(self.monitor.provider)
        self.monitor.wait()

        # Country service
        self.country_service = CountryService(self.config.netuid)
        self.file_monitor.add_file_provider(self.country_service.provider)
        self.country_service.wait()

        # Get the neuron
        self.neuron = await self.database.get_neuron(self.wallet.hotkey.ss58_address)
        btul.logging.info(
            f"Neuron details — Hotkey: {self.neuron.hotkey}, UID: {self.neuron.uid}, IP: {self.neuron.ip}"
        )

        # Get the country
        self.country = self.country_service.get_country(self.dendrite.external_ip)
        btul.logging.debug(f"Validator based in {self.country}")

        # Init wandb.
        if not self.config.wandb.off:
            btul.logging.debug("loading wandb")
            init_wandb(self)

        # Init miners
        self.miners = (await self.database.get_miners()).values()
        btul.logging.debug(f"Miners loaded {len(self.miners)}")

        # Load state
        self.moving_scores = load_state(
            path=self.config.neuron.full_path,
            number_of_uids=self.number_of_uids,
        )
        btul.logging.debug(f"State loaded {self.moving_scores}")

        previous_last_update = 0
        current_block = 0
        while not self.should_exit.is_set():
            try:
                # Ensure the metagraph is ready
                btul.logging.debug("Ensure metagraph readiness")
                await self.database.wait_until_ready("metagraph")

                # Get the last time neurons have been updated
                last_updated = await self.database.get_neuron_last_updated()
                if last_updated == 0:
                    btul.logging.warning(
                        f"Could not get the neuron last updated from redis. Pleaase check your metagraph."
                    )

                # Get min stake to set weight
                min_stake = get_weights_min_stake(substrate=self.subtensor.substrate)
                btul.logging.debug(f"Minimum stake to set weights: {min_stake}")

                # Check if the neurons have changed
                if previous_last_update != last_updated:
                    btul.logging.debug(f"Neurons changed at block #{last_updated}")

                    # At least one neuron has changed
                    previous_last_update and btul.logging.debug(
                        f"Neurons changed, rsync miners"
                    )

                    # Store the new last updated
                    previous_last_update = last_updated

                    # Get the neurons
                    neurons = await self.database.get_neurons()
                    btul.logging.debug(f"Neurons loaded {len(neurons)}")

                    # Refresh the validator neuron
                    self.neuron = neurons.get(self.neuron.hotkey)
                    btul.logging.trace(
                        f"Neuron details — Hotkey: {self.neuron.hotkey}, UID: {self.neuron.uid}, IP: {self.neuron.ip}"
                    )

                    # Check registration
                    btul.logging.debug("Checking registration...")
                    await wait_until_registered(
                        database=self.database,
                        hotkey=self.wallet.hotkey.ss58_address,
                    )

                    # Sync the miners
                    self.miners, moving_scores = await sync_miners(
                        settings=self.settings,
                        database=self.database,
                        neurons=neurons,
                        miners=self.miners,
                        validator=self.neuron,
                        min_stake=min_stake,
                        moving_scores=self.moving_scores.copy(),
                    )

                    # Get the miners with no ips
                    miners_not_serving = [
                        x.uid for x in self.miners if x.ip == "0.0.0.0"
                    ]
                    btul.logging.debug(
                        f"Miners not serving (not selectable): {miners_not_serving}"
                    )

                    # Build the list of uids reset
                    uids_reset = np.flatnonzero(
                        (self.moving_scores != 0) & (moving_scores == 0)
                    )

                    # Save the new moving scores
                    self.moving_scores = moving_scores

                    # Save in database
                    await self.database.update_miners(miners=self.miners)
                    btul.logging.debug(f"Saved miners: {len(self.miners)}")

                    # Log event that have been reset if there are any
                    if uids_reset.size > 0:
                        log_event(self, uids_reset)
                        btul.logging.debug(f"UIDs reset: {uids_reset.tolist()}")

                    # Save state
                    save_state(
                        path=self.config.neuron.full_path,
                        moving_scores=self.moving_scores,
                    )

                # Get the next block
                current_block = self.subtensor.get_current_block()

                # Ensure the subvortex metagraph has been synced within its mandatory interval
                # We add a buffer of 5 minutes to ensure metagraph has time to sync
                if last_updated < current_block - (
                    self.settings.metagraph_sync_interval + 25
                ):
                    btul.logging.warning(
                        f"⚠️ Metagraph may be out of sync! Last update was at block {last_updated}, "
                        f"but current block is {current_block}. Ensure your metagraph is syncing properly."
                    )
                    await asyncio.sleep(1)
                    continue

                # Run multiple forwards.
                coroutines = [forward(self)]
                await asyncio.gather(*coroutines)

                # Check if stop has been requested
                if self.should_exit.is_set():
                    break

                # Get the next block
                current_block = self.subtensor.get_current_block()

                # Set weights if time for it and enough stake
                must_set_weight = should_set_weights(
                    settings=self.settings,
                    subtensor=self.subtensor,
                    neuron=self.neuron,
                    block=current_block,
                    min_stake=min_stake,
                )
                btul.logging.debug(
                    f"Should set weights at block #{current_block}? -> {must_set_weight}"
                )
                if must_set_weight:
                    # Get the weights
                    weights = self.moving_scores
                    btul.logging.debug(f"[{version}] Setting weights {weights}")

                    # Set weights
                    set_weights(
                        settings=self.settings,
                        subtensor=self.subtensor,
                        wallet=self.wallet,
                        uid=self.neuron.uid,
                        weights=weights,
                        version=version,
                    )

                # Check if stop has been requested
                if self.should_exit.is_set():
                    break

                # Rollover wandb to a new run.
                if should_reinit_wandb(self):
                    btul.logging.info("Reinitializing wandb")
                    finish_wandb()
                    init_wandb(self)

                self.step += 1

            except ConnectionRefusedError as e:
                btul.logging.error(f"Connection refused: {e}")
                await asyncio.sleep(1)

            except Exception as ex:
                btul.logging.error(f"Unhandled exception: {ex}")
                btul.logging.debug(traceback.format_exc())

        # Finish wandb
        finish_wandb()

        # Signal the neuron has finished
        self.run_complete.set()

    async def _shutdown(self):
        btul.logging.info("Waiting validator to complete its work...")

        # Wait the neuron to stop
        await self.run_complete.wait()

        btul.logging.info("Shutting down validator...")

        if getattr(self, "subtensor", None):
            self.subtensor.close()
            btul.logging.debug("Subtensor stopped")

        if getattr(self, "dendrite", None):
            await close_dendrite(self.dendrite)

        if getattr(self, "file_monitor", None):
            self.file_monitor.stop()

        btul.logging.info("✅ Shutting down validator completed")


async def main():
    # Initialize miner
    validator = Validator()

    # Get the current asyncio event loop
    loop = asyncio.get_running_loop()

    # Define a signal handler that schedules the shutdown coroutine
    def _signal_handler():
        # Schedule graceful shutdown without blocking the signal handler
        loop.create_task(_shutdown(validator))

    # Register signal handlers for SIGINT (Ctrl+C) and SIGTERM (kill command)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    # Start the main service logic
    await validator.run()

    # Block here until shutdown is signaled and completed
    await shutdown_complete.wait()


async def _shutdown(validator: Validator):
    # Gracefully shut down the service
    await validator.shutdown()

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
