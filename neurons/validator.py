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
import copy
import torch
import asyncio
from redis import asyncio as aioredis
import threading
import bittensor as bt
from typing import List
from shlex import quote
from copy import deepcopy
from pprint import pformat
from traceback import print_exception
from substrateinterface.base import SubstrateInterface

from subnet.shared.checks import check_registration
from subnet.shared.utils import get_redis_password
from subnet.shared.subtensor import get_current_block
from subnet.shared.weights import should_set_weights
from subnet.shared.mock import MockMetagraph, MockDendrite, MockSubtensor

from subnet.validator.config import config, check_config, add_args
from subnet.validator.localisation import get_country, get_localisation
from subnet.validator.forward import forward
from subnet.validator.miner import Miner, get_all_miners
from subnet.validator.state import (
    resync_metagraph_and_miners,
    load_state,
    save_state,
    init_wandb,
    reinit_wandb,
    should_reinit_wandb,
)
from subnet.validator.weights import (
    set_weights_for_validator,
)


class Validator:
    """
    A Neuron instance represents a node in the Bittensor network that performs validation tasks.
    It manages the data validation cycle, including storing, challenging, and retrieving data,
    while also participating in the network consensus.

    Attributes:
        subtensor (bt.subtensor): The interface to the Bittensor network's blockchain.
        wallet (bt.wallet): Cryptographic wallet containing keys for transactions and encryption.
        metagraph (bt.metagraph): Graph structure storing the state of the network.
        database (redis.StrictRedis): Database instance for storing metadata and proofs.
        moving_averaged_scores (torch.Tensor): Tensor tracking performance scores of other nodes.
    """

    @classmethod
    def check_config(cls, config: "bt.Config"):
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        add_args(cls, parser)

    @classmethod
    def config(cls):
        return config(cls)

    subtensor: "bt.subtensor"
    wallet: "bt.wallet"
    metagraph: "bt.metagraph"

    def __init__(self, config=None):
        base_config = copy.deepcopy(config or Validator.config())
        self.config = Validator.config()
        self.config.merge(base_config)
        self.check_config(self.config)
        bt.logging(config=self.config, logging_dir=self.config.neuron.full_path)

        # Init device.
        bt.logging.debug("loading device")
        self.device = torch.device(self.config.neuron.device)
        bt.logging.debug(str(self.device))

        # Init validator wallet.
        bt.logging.debug("loading wallet")
        self.wallet = (
            bt.MockWallet(config=self.config)
            if self.config.mock
            else bt.wallet(config=self.config)
        )
        self.wallet.create_if_non_existent()

        # Init subtensor
        bt.logging.debug("loading subtensor")
        self.subtensor = (
            MockSubtensor(self.config.netuid, wallet=self.wallet) 
            if self.config.mock 
            else bt.subtensor(config=self.config)
        )
        bt.logging.debug(str(self.subtensor))

        # Check registration
        check_registration(self.subtensor, self.wallet, self.config.netuid)

        bt.logging.debug(f"wallet: {str(self.wallet)}")

        # Init metagraph.
        bt.logging.debug("loading metagraph")
        self.metagraph = (
            MockMetagraph(self.config.netuid, subtensor=self.subtensor)
            if self.config.mock
            else bt.metagraph(
                netuid=self.config.netuid, network=self.subtensor.network, sync=False
            )
        )
        self.metagraph.sync(subtensor=self.subtensor)  # Sync metagraph with subtensor.
        bt.logging.debug(str(self.metagraph))

        # Setup database
        bt.logging.info(f"loading database")
        redis_password = get_redis_password(self.config.database.redis_password)
        self.database = aioredis.StrictRedis(
            host=self.config.database.host,
            port=self.config.database.port,
            db=self.config.database.index,
            password=redis_password,
        )
        self.db_semaphore = asyncio.Semaphore()

        # Init Weights.
        bt.logging.debug("loading moving_averaged_scores")
        self.moving_averaged_scores = torch.zeros((self.metagraph.n)).to(self.device)
        bt.logging.debug(str(self.moving_averaged_scores))

        self.uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Running validator on uid: {self.uid}")

        # Dendrite pool for querying the network.
        bt.logging.debug("loading dendrite_pool")
        if self.config.neuron.mock_dendrite_pool:
            self.dendrite = MockDendrite(wallet=self.wallet)
        else:
            self.dendrite = bt.dendrite(wallet=self.wallet)
        bt.logging.debug(str(self.dendrite))

        # Get the validator country
        self.country = get_country(self.dendrite.external_ip)
        country_localisation = get_localisation(self.country)
        country_name = (
            country_localisation["country"] if country_localisation else "None"
        )
        bt.logging.debug(f"Validator based in {country_name}")

        # Init wandb.
        if not self.config.wandb.off:
            bt.logging.debug("loading wandb")
            init_wandb(self)

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

    async def run(self):
        bt.logging.info("run()")

        # Init miners
        self.miners = await get_all_miners(self)
        bt.logging.debug(f"Miners loaded {len(self.miners)}")

        load_state(self)

        bt.logging.info("starting subscription handler")
        self.run_subscription_thread()

        try:
            while 1:
                start_epoch = time.time()

                await resync_metagraph_and_miners(self)
                prev_set_weights_block = self.metagraph.last_update[self.uid].item()

                # --- Wait until next step epoch.
                current_block = self.subtensor.get_current_block()
                while current_block - self.prev_step_block < 3:
                    # --- Wait for next block.
                    time.sleep(1)
                    current_block = self.subtensor.get_current_block()

                time.sleep(5)
                if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
                    raise Exception(
                        f"Validator is not registered - hotkey {self.wallet.hotkey.ss58_address} not in metagraph"
                    )

                bt.logging.info(
                    f"step({self.step}) block({get_current_block(self.subtensor)})"
                )

                # Run multiple forwards.
                async def run_forward():
                    coroutines = [
                        forward(self)
                        for _ in range(self.config.neuron.num_concurrent_forwards)
                    ]
                    await asyncio.gather(*coroutines)

                self.loop.run_until_complete(run_forward())

                # Set the weights on chain.
                bt.logging.info("Checking if should set weights")
                validator_should_set_weights = should_set_weights(
                    get_current_block(self.subtensor),
                    prev_set_weights_block,
                    360,  # tempo
                    self.config.neuron.disable_set_weights,
                )
                bt.logging.debug(
                    f"Should validator check weights? -> {validator_should_set_weights}"
                )
                if validator_should_set_weights:
                    bt.logging.debug(f"Setting weights {self.moving_averaged_scores}")
                    set_weights_for_validator(
                        subtensor=self.subtensor,
                        wallet=self.wallet,
                        metagraph=self.metagraph,
                        netuid=self.config.netuid,
                        moving_averaged_scores=self.moving_averaged_scores,
                    )
                    prev_set_weights_block = get_current_block(self.subtensor)
                    save_state(self)

                # Rollover wandb to a new run.
                if should_reinit_wandb(self):
                    bt.logging.info("Reinitializing wandb")
                    reinit_wandb(self)

                self.prev_step_block = get_current_block(self.subtensor)
                if self.config.neuron.verbose:
                    bt.logging.debug(f"block at end of step: {self.prev_step_block}")
                    bt.logging.debug(f"Step took {time.time() - start_epoch} seconds")
                self.step += 1

        except Exception as err:
            bt.logging.error("Error in training loop", str(err))
            bt.logging.debug(print_exception(type(err), err, err.__traceback__))

        # After all we have to ensure subtensor connection is closed properly
        finally:
            if hasattr(self, "subtensor"):
                bt.logging.debug("Closing subtensor connection")
                self.subtensor.close()
                self.stop_subscription_thread()

            if self.wandb is not None:
                bt.logging.debug("Finishing wandb run")
                self.wandb.finish()

    # TODO: After investigation done and decision taken, remove or change it
    def start_event_subscription(self):
        """
        Starts the subscription handler in a background thread.
        """
        substrate = SubstrateInterface(
            ss58_format=bt.__ss58_format__,
            use_remote_preset=True,
            url=self.subtensor.chain_endpoint,
            type_registry=bt.__type_registry__,
        )
        self.subscription_substrate = substrate

        def neuron_registered_subscription_handler(obj, update_nr, subscription_id):
            block_no = obj["header"]["number"]
            block_hash = substrate.get_block_hash(block_id=block_no)
            bt.logging.debug(f"subscription block hash: {block_hash}")
            events = substrate.get_events(block_hash)

            for event in events:
                event_dict = event["event"].decode()
                if event_dict["event_id"] == "NeuronRegistered":
                    netuid, uid, hotkey = event_dict["attributes"]
                    if int(netuid) == 21:
                        self.log(
                            f"NeuronRegistered Event {uid}! Rebalancing data...\n"
                            f"{pformat(event_dict)}\n"
                        )

                        self.last_registered_block = block_no
                        self.rebalance_queue.append(hotkey)

            # If we have some hotkeys deregistered, and it's been 5 blocks since we've caught a registration: rebalance
            if (
                len(self.rebalance_queue) > 0
                and self.last_registered_block + 5 <= block_no
            ):
                hotkeys = deepcopy(self.rebalance_queue)
                self.rebalance_queue.clear()
                self.log(f"Running rebalance in separate process on hotkeys {hotkeys}")

                # Fire off the script
                hotkeys_str = ",".join(map(str, hotkeys))
                hotkeys_arg = quote(hotkeys_str)
                # subprocess.Popen(
                #     [
                #         self.rebalance_script_path,
                #         hotkeys_arg,
                #         self.subtensor.chain_endpoint,
                #         str(self.config.database.index),
                #     ]
                # )

        substrate.subscribe_block_headers(neuron_registered_subscription_handler)

    def run_subscription_thread(self):
        """
        Start the block header subscription handler in a separate thread.
        """
        if not self.subscription_is_running:
            self.subscription_thread = threading.Thread(
                target=self.start_event_subscription, daemon=True
            )
            self.subscription_thread.start()
            self.subscription_is_running = True
            bt.logging.debug("Started subscription handler.")

    def stop_subscription_thread(self):
        """
        Stops the subscription handler that is running in the background thread.
        """
        if self.subscription_is_running:
            bt.logging.debug("Stopping subscription in background thread.")
            self.should_exit = True
            self.subscription_thread.join(5)
            self.subscription_is_running = False
            self.subscription_substrate.close()
            bt.logging.debug("Stopped subscription handler.")


if __name__ == "__main__":
    asyncio.run(Validator().run())
