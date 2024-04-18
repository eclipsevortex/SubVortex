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

import sys
import typing
import time
import torch
import asyncio
import bittensor as bt
import threading
import traceback

from subnet.protocol import Score

from subnet.shared.checks import check_registration

from subnet import __version__ as THIS_VERSION
from subnet.miner import run
from subnet.miner.config import (
    config,
    check_config,
    add_args,
)
from subnet.miner.utils import load_request_log


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

        # Init device.
        bt.logging.debug("loading device")
        self.device = torch.device(self.config.miner.device)
        bt.logging.debug(str(self.device))

        # Init subtensor
        bt.logging.debug("loading subtensor")
        self.subtensor = (
            bt.MockSubtensor()
            if self.config.miner.mock_subtensor
            else bt.subtensor(config=self.config, network="local")
        )
        bt.logging.debug(str(self.subtensor))
        self.current_block = self.subtensor.get_current_block()

        # Init wallet.
        bt.logging.debug("loading wallet")
        self.wallet = bt.wallet(config=self.config)
        self.wallet.create_if_non_existent()
        check_registration(self.subtensor, self.wallet, self.config.netuid)
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

        # The axon handles request processing, allowing validators to send this process requests.
        self.axon = bt.axon(
            wallet=self.wallet, config=self.config, external_ip=bt.net.get_external_ip()
        )
        bt.logging.info(f"Axon {self.axon}")

        # Attach determiners which functions are called when servicing a request.
        bt.logging.info("Attaching forward functions to axon.")
        self.axon.attach(
            forward_fn=self._score,
            blacklist_fn=self.blacklist_score,
        )

        # Serve passes the axon information to the network + netuid we are hosting on.
        # This will auto-update if the axon port of external ip have changed.
        bt.logging.info(
            f"Serving axon {self.axon} on network: {self.subtensor.chain_endpoint} with netuid: {self.config.netuid}"
        )
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)

        # Check there is not another miner running on the machine
        number_of_miners = len(
            [axon for axon in self.metagraph.axons if self.axon.external_ip == axon.ip]
        )
        if number_of_miners > 1:
            bt.logging.error(
                "At least one miner is already running on this machine. If you run more than one miner you will penalise all of your miners until you get de-registered or start each miner on a unique machine"
            )
            sys.exit(1)

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

        self.request_log = load_request_log(self.config.miner.request_log_path)

    def _score(self, synapse: Score) -> Score:
        validator_uid = synapse.validator_uid

        if synapse.owner:
            bt.logging.info(f"[{validator_uid}] Miner owns the subtensor")
        elif synapse.owner == False:
            bt.logging.error(f"[{validator_uid}] Miner does not own the subtensor")

        if synapse.verified:
            bt.logging.info(f"[{validator_uid}] Miner/Subtensor verified")
        elif synapse.verified == False:
            bt.logging.error(f"[{validator_uid}] {synapse.reason or 'unknown'}")

        if synapse.count > 1:
            bt.logging.error(
                f"[{validator_uid}] {synapse.count} miners are running on this machine"
            )

        bt.logging.info(f"[{validator_uid}] Availability score {synapse.availability}")
        bt.logging.info(f"[{validator_uid}] Latency score {synapse.latency}")
        bt.logging.info(f"[{validator_uid}] Reliability score {synapse.reliability}")
        bt.logging.info(f"[{validator_uid}] Distribution score {synapse.distribution}")
        bt.logging.success(f"[{validator_uid}] Score {synapse.score}")

        synapse.version = THIS_VERSION

        return synapse

    def blacklist_score(self, synapse: Score) -> typing.Tuple[bool, str]:
        caller = synapse.dendrite.hotkey

        if caller in self.config.blacklist.blacklist_hotkeys:
            return True, f"Hotkey {caller} in blacklist."
        elif caller in self.config.blacklist.whitelist_hotkeys:
            return False, f"Hotkey {caller} in whitelist."

        if caller not in self.metagraph.hotkeys:
            bt.logging.trace(f"Blacklisting unrecognized hotkey {caller}")
            return True, "Unrecognized hotkey"

        bt.logging.trace(f"Not Blacklisting recognized hotkey {caller}")
        return False, "Hotkey recognized!"

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
