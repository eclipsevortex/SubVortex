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
        self.neuron = (await self.database.get_neuron(self.wallet.hotkey.ss58_address)) or Neuron.create_empty()
        btul.logging.info(
            f"Neuron details — Hotkey: {self.neuron.hotkey}, UID: {self.neuron.uid}, IP: {self.neuron.ip}"
        )

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
                    btul.logging.trace(f"Neurons loaded {len(neurons)}")

                    # Refresh the validator neuron
                    self.neuron = neurons.get(self.neuron.hotkey, Neuron.create_empty())
                    btul.logging.trace(
                        f"Neuron details — Hotkey: {self.neuron.hotkey}, UID: {self.neuron.uid}, IP: {self.neuron.ip}"
                    )

                    if not self.settings.dry_run:
                        # Check registration
                        btul.logging.debug("Checking registration...")
                        await wait_until_registered(
                            database=self.database,
                            hotkey=self.wallet.hotkey.ss58_address,
                        )

                    # Get the locations
                    locations = self.country_service.get_locations()
                    btul.logging.trace(f"Locations loaded {len(locations)}")

                    # Sync the miners
                    self.miners, self.moving_scores = await sync_miners(
                        settings=self.settings,
                        database=self.database,
                        neurons=neurons,
                        miners=self.miners,
                        validator=self.neuron,
                        locations=locations,
                        min_stake=min_stake,
                        moving_scores=self.moving_scores,
                    )

                    # Save in database
                    await self.database.update_miners(miners=self.miners)
                    btul.logging.trace(f"Miners saved")

                    # Save state
                    save_state(
                        path=self.config.neuron.full_path,
                        moving_scores=self.moving_scores,
                    )
                    btul.logging.trace(f"State saved")

                # Get the next block
                current_block = self.subtensor.get_current_block()

                # Ensure the subvortex metagraph has been synced within its mandatory interval
                # We add a buffer of 5 minutes to ensure metagraph has time to sync
                assert last_updated >= (
                    current_block - (self.settings.metagraph_sync_interval + 25)
                ), (
                    f"⚠️ Metagraph may be out of sync! Last update was at block {last_updated}, "
                    f"but current block is {current_block}. Ensure your metagraph is syncing properly."
                )

                # Wait until next step epoch.
                current_block = get_next_block(
                    subtensor=self.subtensor, block=current_block
                )

                # Run multiple forwards.
                coroutines = [forward(self)]
                await asyncio.gather(*coroutines)

                # Check if stop has been requested
                if self.should_exit.is_set():
                    break

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

            except AssertionError:
                # We already display a log, so need to do more here
                pass

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


if __name__ == "__main__":
    validator = Validator()

    def _handle_signal(sig, frame):
        loop.call_soon_threadsafe(lambda: asyncio.create_task(validator._shutdown()))

    # Create and set a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Register signal handlers (in main thread)
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        # Run the miner
        loop.run_until_complete(validator.run())

    except Exception as e:
        btul.logging.error(f"Unhandled exception: {e}")
        btul.logging.debug(traceback.format_exc())
    finally:
        # Cleanup async generators and close loop
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
