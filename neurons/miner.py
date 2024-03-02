# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

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

import sys
import typing
import time
import torch
import asyncio
import bittensor as bt
import threading
import traceback
from urllib.parse import urlparse

from subnet.protocol import IsAlive, Key, Subtensor, Challenge

from subnet.shared.key import generate_ssh_key, clean_ssh_key
from subnet.shared.checks import check_environment

from subnet.miner import run
from subnet.miner.config import (
    config,
    check_config,
    add_args,
)
from subnet.miner.utils import (
    update_storage_stats,
    load_request_log,
)


class Miner:
    @classmethod
    def check_config(cls, config: "bt.Config"):
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
            bt.Config: The configuration object for the neuron.

        This class method returns the neuron's configuration, which is used throughout the neuron's lifecycle
        for various functionalities and operations.
        """
        return config(cls)

    subtensor: "bt.subtensor"
    wallet: "bt.wallet"
    metagraph: "bt.metagraph"

    def __init__(self):
        self.config = Miner.config()
        self.check_config(self.config)
        bt.logging(config=self.config, logging_dir=self.config.miner.full_path)
        bt.logging.info(f"{self.config}")

        try:
            asyncio.run(check_environment(self.config.database.redis_conf_path))
        except AssertionError as e:
            bt.logging.warning(
                f"Something is missing in your environment: {e}. Please check your configuration, use the README for help, and try again."
            )

        bt.logging.info("miner.__init__()")

        # Init device.
        bt.logging.debug("loading device")
        self.device = torch.device(self.config.miner.device)
        bt.logging.debug(str(self.device))

        # Init subtensor
        bt.logging.debug("loading subtensor")
        self.subtensor = bt.subtensor(config=self.config)
        bt.logging.debug(str(self.subtensor))
        self.current_block = self.subtensor.get_current_block()

        # Init wallet.
        bt.logging.debug("loading wallet")
        self.wallet = bt.wallet(config=self.config)
        self.wallet.create_if_non_existent()
        if not self.config.wallet._mock:
            if not self.subtensor.is_hotkey_registered_on_subnet(
                hotkey_ss58=self.wallet.hotkey.ss58_address, netuid=self.config.netuid
            ):
                raise Exception(
                    f"Wallet not currently registered on netuid {self.config.netuid}, please first register wallet before running"
                )

        bt.logging.debug(f"wallet: {str(self.wallet)}")

        # Init metagraph.
        bt.logging.debug("loading metagraph")
        self.metagraph = bt.metagraph(
            netuid=self.config.netuid, network=self.subtensor.network, sync=False
        )  # Make sure not to sync without passing subtensor
        self.metagraph.sync(subtensor=self.subtensor)  # Sync metagraph with subtensor.
        bt.logging.debug(str(self.metagraph))

        self.my_subnet_uid = self.metagraph.hotkeys.index(
            self.wallet.hotkey.ss58_address
        )
        bt.logging.info(f"Running miner on uid: {self.my_subnet_uid}")

        # parsed_url = urlparse(self.subtensor.chain_endpoint)
        # ip = (
        #     self.axon.external_ip
        #     if parsed_url.hostname == "127.0.0.1"
        #     else parsed_url.hostname
        # )

        # The axon handles request processing, allowing validators to send this process requests.
        self.axon = bt.axon(wallet=self.wallet, config=self.config)
        bt.logging.info(f"Axon {self.axon}")

        # Attach determiners which functions are called when servicing a request.
        bt.logging.info("Attaching forward functions to axon.")
        self.axon.attach(
            forward_fn=self._is_alive,
            blacklist_fn=self.blacklist_isalive,
        )
        # .attach(
        #     forward_fn=self._subtensor,
        #     blacklist_fn=self.blacklist_subtensor,
        # )
        # .attach(
        #     forward_fn=self._generate_key,
        #     blacklist_fn=self.blacklist_generate_key,
        # ).attach(
        #     forward_fn=self._subtensor,
        #     blacklist_fn=self.blacklist_subtensor,
        # ).attach(
        #     forward_fn=self._challenge,
        #     blacklist_fn=self.blacklist_challenge,
        # )

        # Serve passes the axon information to the network + netuid we are hosting on.
        # This will auto-update if the axon port of external ip have changed.
        bt.logging.info(
            f"Serving axon {self.axon} on network: {self.subtensor.chain_endpoint} with netuid: {self.config.netuid}"
        )
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)

        # Start  starts the miner's axon, making it active on the network.
        bt.logging.info(f"Starting axon server on port: {self.config.axon.port}")
        self.axon.start()

        # Init the event loop.
        self.loop = asyncio.get_event_loop()

        # Instantiate runners
        self.should_exit: bool = False
        self.is_running: bool = False
        self.thread: threading.Thread = None
        self.lock = asyncio.Lock()
        self.request_timestamps: typing.Dict = {}

        self.step = 0

        # Init the miner's storage request tracker
        self.request_count = 0
        self.start_request_count_timer()
        self.requests_per_hour = []
        self.average_requests_per_hour = 0

        # Init the miner's storage usage tracker
        update_storage_stats(self)

        self.rate_limiters = {}
        self.request_log = load_request_log(self.config.miner.request_log_path)

    def _is_alive(self, synapse: IsAlive) -> IsAlive:
        bt.logging.info("I'm alive!")
        synapse.answer = "alive"
        return synapse

    def blacklist_isalive(self, synapse: IsAlive) -> typing.Tuple[bool, str]:
        return False, synapse.dendrite.hotkey

    async def _generate_key(self, synapse: Key) -> Key:
        synapse_type = "Save" if synapse.generate else "Clean"
        bt.logging.info(f"[Key/{synapse_type}] Synapse received")
        if synapse.generate:
            generate_ssh_key(synapse.validator_public_key)
        else:
            clean_ssh_key(synapse.validator_public_key)
        bt.logging.info(f"[Key/{synapse_type}] Synapse proceed")
        return synapse

    async def blacklist_generate_key(self, synapse: Key) -> typing.Tuple[bool, str]:
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            # Ignore requests from unrecognized entities.
            bt.logging.trace(
                f"Blacklisting unrecognized hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"

        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    async def _subtensor(self, synapse: Subtensor) -> Subtensor:
        bt.logging.info("[Subtensor] Synapse received")
        parsed_url = urlparse(self.subtensor.chain_endpoint)
        ip = (
            self.axon.external_ip
            if parsed_url.hostname == "127.0.0.1"
            else parsed_url.hostname
        )
        synapse.subtensor_ip = ip
        bt.logging.success("[Subtensor] Synapse proceed")
        return synapse

    async def blacklist_subtensor(self, synapse: Subtensor) -> typing.Tuple[bool, str]:
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            # Ignore requests from unrecognized entities.
            bt.logging.trace(
                f"Blacklisting unrecognized hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"

        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    async def _challenge(self, synapse: Challenge) -> Challenge:
        bt.logging.info("[Challenge] Synapse received")
        block = self.subtensor.get_current_block()
        synapse.answer = f"{block}"
        bt.logging.info("[Challenge] Synapse proceed")
        return synapse

    async def blacklist_challenge(self, synapse: Challenge) -> typing.Tuple[bool, str]:
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            # Ignore requests from unrecognized entities.
            bt.logging.trace(
                f"Blacklisting unrecognized hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"

        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    def start_request_count_timer(self):
        """
        Initializes and starts a timer for tracking the number of requests received by the miner in an hour.

        This method sets up a one-hour timer that, upon expiration, calls the `reset_request_count` method to log
        the number of requests received and reset the count for the next hour. The timer is set to run in a separate
        thread to avoid blocking the main execution.

        Usage:
            Should be called during the initialization of the miner to start tracking requests per hour.
        """
        self.request_count_timer = threading.Timer(3600, self.reset_request_count)
        self.request_count_timer.start()

    def reset_request_count(self):
        """
        Logs the number of requests received in the last hour and resets the count.

        This method is automatically called when the one-hour timer set by `start_request_count_timer` expires.
        It logs the count of requests received in the last hour and then resets the count. Additionally, it
        restarts the timer for the next hour.

        Usage:
            This method is intended to be called automatically by a timer and typically should not be called directly.
        """
        bt.logging.info(
            f"Number of requests received in the last hour: {self.request_count}"
        )
        self.requests_per_hour.append(self.request_count)
        bt.logging.info(f"Requests per hour: {self.requests_per_hour}")
        self.average_requests_per_hour = sum(self.requests_per_hour) / len(
            self.requests_per_hour
        )
        bt.logging.info(f"Average requests per hour: {self.average_requests_per_hour}")
        self.request_count = 0
        self.start_request_count_timer()

    def run(self):
        run(self)

    def run_in_background_thread(self):
        """
        Starts the miner's operations in a separate background thread.
        This is useful for non-blocking operations.
        """
        if not self.is_running:
            bt.logging.debug("Starting miner in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            bt.logging.debug("Started")

    def stop_run_thread(self):
        """
        Stops the miner's operations that are running in the background thread.
        """
        if self.is_running:
            bt.logging.debug("Stopping miner in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def __enter__(self):
        """
        Starts the miner's operations in a background thread upon entering the context.
        This method facilitates the use of the miner in a 'with' statement.
        """
        self.run_in_background_thread()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the miner's background operations upon exiting the context.
        This method facilitates the use of the miner in a 'with' statement.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
                      None if the context was exited without an exception.
            exc_value: The instance of the exception that caused the context to be exited.
                       None if the context was exited without an exception.
            traceback: A traceback object encoding the stack trace.
                       None if the context was exited without an exception.
        """
        self.stop_run_thread()


def run_miner():
    """
    Main function to run the neuron.

    This function initializes and runs the neuron. It handles the main loop, state management, and interaction
    with the Bittensor network.
    """

    Miner().run_in_background_thread()

    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        bt.logging.info("Keyboard interrupt detected, exiting.")
        sys.exit(0)
    except Exception as e:
        bt.logging.error(traceback.format_exc())
        bt.logging.error(f"Unhandled exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_miner()
