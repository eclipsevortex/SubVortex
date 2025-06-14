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
import bittensor.core.async_subtensor as btcas
import bittensor.core.metagraph as btcm
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw
import bittensor_wallet.mock as btwm
from dotenv import load_dotenv

from subvortex.core.version import get_version
from subvortex.core.shared.mock import MockSubtensor
from subvortex.core.shared.neuron import wait_until_registered
from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.dendrite import close_dendrite
from subvortex.core.core_bittensor.subtensor import (
    get_number_of_uids,
    get_weights_min_stake,
)
from subvortex.validator.neuron.src.config import config, check_config, add_args
from subvortex.validator.neuron.src.models.miner import Miner
from subvortex.validator.neuron.src.weights import (
    set_weights,
)
from subvortex.validator.neuron.src.settings import Settings
from subvortex.validator.neuron.src.database import Database
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
            else btcas.AsyncSubtensor(config=self.config)
        )
        btul.logging.debug(str(self.subtensor))

        # Initialize the database
        btul.logging.info("loading database")
        self.database = Database(settings=self.settings)

        current_block = 0
        while not self.should_exit.is_set():
            try:
                # Ensure the metagraph is ready
                btul.logging.debug(
                    "Ensure metagraph readiness", prefix=self.settings.logging_name
                )
                await self.database.wait_until_ready(
                    name="metagraph", event=self.should_exit
                )

                # Check registration
                btul.logging.debug(
                    "Checking registration...", prefix=self.settings.logging_name
                )
                await wait_until_registered(database=self.database, hotkey=self.hotkey)

                # Get the current block
                current_block = await self.subtensor.get_current_block()
                btul.logging.debug(
                    f"📦 Block #{current_block}", prefix=self.settings.logging_name
                )

                # Get the last time the metagraph has been updated
                last_updated = await self.database.get_neuron_last_updated()
                btul.logging.debug(
                    f"Metagraph last update: {last_updated}",
                    prefix=self.settings.logging_name,
                )

                # Compute the cutoff
                sync_cutoff = last_updated + self.settings.metagraph_sync_interval + 25
                btul.logging.debug(
                    f"Metagraph sync cutoff: {sync_cutoff}",
                    prefix=self.settings.logging_name,
                )

                # Check is metagraph has been updated within its sync interval
                if current_block > sync_cutoff:
                    btul.logging.warning(
                        f"⚠️ Metagraph may be out of sync! Last update was at block {last_updated}, "
                        f"but current block is {current_block}. Ensure your metagraph is syncing properly.",
                        prefix=self.settings.logging_name,
                    )
                    await asyncio.sleep(1)
                    continue

                # Get min stake to set weight
                min_stake = await get_weights_min_stake(subtensor=self.subtensor)
                btul.logging.debug(f"Minimum stake to set weights: {min_stake}")

                # Get the neuron
                neuron = await self.database.get_neuron(
                    hotkey=self.wallet.hotkey.ss58_address
                )

                # TODO: Clean prune miners!!
                # TODO: Reset miners that have changed country?

                # Set weights if time for it and enough stake
                must_set_weight = should_set_weights(
                    settings=self.settings,
                    subtensor=self.subtensor,
                    neuron=neuron,
                    block=current_block,
                    min_stake=min_stake,
                )
                btul.logging.debug(
                    f"Should set weights at block #{current_block}? -> {must_set_weight}"
                )
                if must_set_weight:
                    # Get the number of uids
                    number_of_uids = await get_number_of_uids(
                        subtensor=self.subtensor, netuid=self.settings.netuid
                    )
                    btul.logging.debug(f"# of uids: {number_of_uids}")

                    # Get the miners
                    miners = await self.database.get_miners()
                    btul.logging.debug(f"# of miners: {len(miners)}")

                    # Build the weights
                    weights = np.array(
                        [
                            next(
                                (m.moving_score for m in miners.values() if m.uid == i),
                                0.0,
                            )
                            for i in range(number_of_uids)
                        ],
                        dtype=np.float32,
                    )
                    btul.logging.debug(f"[{version}] Setting weights {weights}")

                    # Set weights
                    set_weights(
                        settings=self.settings,
                        subtensor=self.subtensor,
                        wallet=self.wallet,
                        uid=neuron.uid,
                        weights=weights,
                        version=version,
                    )

            except ConnectionRefusedError as e:
                btul.logging.error(f"Connection refused: {e}")
                await asyncio.sleep(1)

            except Exception as ex:
                btul.logging.error(f"Unhandled exception: {ex}")
                btul.logging.debug(traceback.format_exc())

        # Signal the neuron has finished
        self.run_complete.set()

    async def shutdown(self):
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
