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
import asyncio
import traceback
import threading
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
from subvortex.core.shared.checks import check_registration
from subvortex.core.shared.subtensor import get_current_block
from subvortex.core.shared.mock import MockMetagraph, MockDendrite, MockSubtensor
from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.dendrite import SubVortexDendrite
from subvortex.core.version import to_spec_version

from subvortex.validator.version import __version__ as THIS_VERSION

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
from subvortex.validator.neuron.src.miner import get_miners, sync_miners
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

        # Display the settings
        btul.logging.info(f"validator settings: {self.settings}")

        # Show miner version
        btul.logging.debug(f"validator version {THIS_VERSION}")

        # Init validator wallet.
        btul.logging.debug(f"loading wallet")
        self.wallet = (
            btwm.get_mock_wallet()
            if self.config.mock
            else btw.Wallet(config=self.config)
        )
        self.wallet.create_if_non_existent()

        # Init subtensor
        btul.logging.debug("loading subtensor")
        self.subtensor = (
            MockSubtensor(self.config.netuid, wallet=self.wallet)
            if self.config.mock
            else btcs.Subtensor(config=self.config)
        )
        btul.logging.debug(str(self.subtensor))

        # Check registration
        btul.logging.debug("checking registration")
        check_registration(self.subtensor, self.wallet, self.config.netuid)

        btul.logging.debug(f"wallet: {str(self.wallet)}")

        # Init metagraph.
        btul.logging.debug("loading metagraph")
        self.metagraph = (
            MockMetagraph(self.config.netuid, subtensor=self.subtensor)
            if self.config.mock
            else btcm.Metagraph(
                netuid=self.config.netuid, network=self.subtensor.network, sync=False
            )
        )
        self.metagraph.sync(subtensor=self.subtensor)  # Sync metagraph with subtensor.
        btul.logging.debug(str(self.metagraph))

        # Initialize the database
        btul.logging.info("loading database")
        self.database = Database(settings=self.settings)

        # Init Weights.
        btul.logging.debug("loading moving_averaged_scores")
        self.moving_averaged_scores = np.zeros((self.metagraph.n))
        btul.logging.debug(str(self.moving_averaged_scores))

        self.uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        btul.logging.info(f"Running validator on uid: {self.uid}")

        # Dendrite pool for querying the network.
        btul.logging.debug("loading dendrite_pool")
        if self.config.neuron.mock_dendrite_pool:
            self.dendrite = MockDendrite(wallet=self.wallet)
        else:
            self.dendrite = SubVortexDendrite(
                version=to_spec_version(THIS_VERSION), wallet=self.wallet
            )
        btul.logging.debug(str(self.dendrite))

        # Init the event loop.
        self.loop = asyncio.get_event_loop()

        self.prev_step_block = get_current_block(self.subtensor)
        self.step = 0

        # Instantiate runners
        self.should_exit: bool = False
        self.subscription_is_running: bool = False
        self.subscription_thread: threading.Thread = None
        self.last_registered_block = 0
        self.rebalance_queue = []
        self.miners: List[Miner] = []
        self.last_upgrade_country = None

    async def run(self):
        btul.logging.info("run()")

        # Check if the connection to the database is successful
        await check_redis_connection(port=self.settings.redis_port)

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
        btul.logging.debug(f"Validator based in {self.neuron.country}")

        # Init wandb.
        if not self.config.wandb.off:
            btul.logging.debug("loading wandb")
            init_wandb(self)

        # Init miners
        self.miners = await get_miners(database=self.database)
        btul.logging.debug(f"Miners loaded {len(self.miners)}")

        # Load the state
        load_state(self)

        previous_last_update = None
        try:
            while 1:
                start_epoch = time.time()

                # Get the last time neurons have been updated
                last_update = await self.database.get_neuron_last_update()
                btul.logging.debug(f"Neurons last updated #{last_update}")

                # Avoir to triggers the following on start
                previous_last_update = previous_last_update or last_update

                # Check if the neurons have changed
                if previous_last_update != last_update:
                    # At least one neuron has changed
                    btul.logging.debug(f"Neurons changed, rsync miners")

                    # Get the neurons
                    neurons = await self.database.get_neurons()
                    btul.logging.debug(f"Neurons loaded {len(neurons)}")

                    # Refresh the validator neuron
                    self.neuron = neurons.get(self.neuron.hotkey)

                    # Get the locations
                    locations = self.country_service.get_locations()
                    btul.logging.debug(f"Locations loaded {len(locations)}")

                    # Sync the miners
                    await sync_miners(
                        database=self.database,
                        neurons=neurons,
                        miners=self.miners,
                        validator=self.neuron,
                        locations=locations,
                    )

                    # Save in database
                    await self.database.update_miners(miners=self.miners)

                # --- Wait until next step epoch.
                current_block = self.subtensor.get_current_block()
                while current_block - self.prev_step_block < 3:
                    # --- Wait for next block.
                    time.sleep(1)
                    current_block = self.subtensor.get_current_block()

                time.sleep(5)

                # --- Check validator is registered
                neuron = await self.database.get_neuron(self.wallet.hotkey.ss58_address)
                if neuron is None:
                    raise Exception(f"Validator is not registered")

                btul.logging.info(
                    f"step({self.step}) block({get_current_block(self.subtensor)})"
                )

                # Run multiple forwards.
                coroutines = [forward(self)]
                await asyncio.gather(*coroutines)

                # Set the weights on chain.
                btul.logging.info("Checking if should set weights")
                must_set_weight = should_set_weights(
                    settings=self.settings,
                    subtensor=self.subtensor,
                    uid=self.neuron.uid,
                    block=current_block,
                )
                btul.logging.debug(
                    f"Should validator check weights? -> {must_set_weight}"
                )
                if must_set_weight:
                    btul.logging.debug(f"Setting weights {self.moving_averaged_scores}")
                    set_weights(
                        settings=self.settings,
                        subtensor=self.subtensor,
                        wallet=self.wallet,
                        uid=self.neuron.uid,
                        moving_scores=self.moving_averaged_scores,
                    )
                    save_state(self)

                # Rollover wandb to a new run.
                if should_reinit_wandb(self):
                    btul.logging.info("Reinitializing wandb")
                    finish_wandb()
                    init_wandb(self)

                self.prev_step_block = get_current_block(self.subtensor)
                if self.config.neuron.verbose:
                    btul.logging.debug(f"block at end of step: {self.prev_step_block}")
                    btul.logging.debug(f"Step took {time.time() - start_epoch} seconds")

                self.step += 1

        except Exception as err:
            btul.logging.error("Unhandled exception", str(err))
            btul.logging.debug(traceback.format_exc())
            finish_wandb()

        # After all we have to ensure subtensor connection is closed properly
        finally:
            if self.file_monitor:
                self.file_monitor.stop()

            if self.loop.is_running():
                self.loop.stop()

            if not self.loop.is_closed():
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                self.loop.close()

            if hasattr(self, "subtensor"):
                btul.logging.debug("Closing subtensor connection")
                self.subtensor.close()


if __name__ == "__main__":
    asyncio.run(Validator().run())
