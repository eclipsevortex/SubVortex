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
from subnet.shared.subtensor import get_hyperparameter_value
from subnet.shared.substrate import get_weights_min_stake

from subnet.bittensor.metagraph import SubVortexMetagraph
from subnet.bittensor.axon import SubVortexAxon
from subnet.bittensor.synapse import Synapse

from subnet import __version__ as THIS_VERSION
from subnet.file.file_monitor import FileMonitor
from subnet.firewall.firewall_factory import (
    create_firewall_tool,
    create_firewall_observer,
)
from subnet.miner.run import run
from subnet.miner.firewall import Firewall
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
    metagraph: SubVortexMetagraph

    def __init__(self):
        self.config = Miner.config()
        self.check_config(self.config)
        bt.logging(
            config=self.config,
            logging_dir=self.config.miner.full_path,
            debug=True,
        )
        bt.logging.set_trace(self.config.logging.trace)
        bt.logging._stream_formatter.set_trace(self.config.logging.trace)
        bt.logging.info(f"{self.config}")

        # Show miner version
        bt.logging.debug(f"miner version {THIS_VERSION}")

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
        self.metagraph = SubVortexMetagraph(
            netuid=self.config.netuid, network=self.subtensor.network, sync=False
        )  # Make sure not to sync without passing subtensor
        self.metagraph.sync(subtensor=self.subtensor)  # Sync metagraph with subtensor.
        bt.logging.debug(str(self.metagraph))

        self.uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Running miner on uid: {self.uid}")

        # The axon handles request processing, allowing validators to send this process requests.
        self.axon = SubVortexAxon(
            wallet=self.wallet,
            config=self.config,
            external_ip=bt.utils.networking.get_external_ip(),
            blacklist_fn=self._blacklist,
        )
        bt.logging.info(f"Axon {self.axon}")
        bt.logging.info(f"Axon version {self.axon.info().version}")

        # Attach determiners which functions are called when servicing a request.
        bt.logging.info("Attaching forward functions to axon.")
        self.axon.attach(
            forward_fn=self._score,
            blacklist_fn=self._blacklist_score,
        )

        # Serve passes the axon information to the network + netuid we are hosting on.
        # This will auto-update if the axon port of external ip have changed.
        bt.logging.info(
            f"Serving axon {self.axon} on network: {self.subtensor.chain_endpoint} with netuid: {self.config.netuid}"
        )
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)

        # Check there is not another miner running on the machine
        bt.logging.debug(f"Checking number of miners on same ip")
        number_of_miners = len(
            [axon for axon in self.metagraph.axons if self.axon.external_ip == axon.ip]
        )
        if number_of_miners > 1:
            bt.logging.error(
                "At least one miner is already running on this machine. If you run more than one miner you will penalise all of your miners until you get de-registered or start each miner on a unique machine"
            )
            sys.exit(1)

        # File monitor
        self.file_monitor = FileMonitor()
        self.file_monitor.start()

        # Firewall
        self.firewall = None
        if self.config.firewall.on:
            bt.logging.debug(
                f"Starting firewall on interface {self.config.firewall.interface}"
            )
            self.firewall = Firewall(
                observer=create_firewall_observer(),
                tool=create_firewall_tool(),
                port=self.axon.external_port,
                interface=self.config.firewall.interface,
            )
            self.update_firewall()
            self.file_monitor.add_file_provider(self.firewall.provider)
            self.firewall.start()

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
        self.previous_last_updates = []

        self.step = 0

        self.request_log = load_request_log(self.config.miner.request_log_path)

    def _blacklist(self, synapse: Synapse) -> typing.Tuple[bool, str]:
        caller = synapse.dendrite.hotkey
        caller_version = synapse.dendrite.neuron_version or 0
        synapse_type = type(synapse).__name__

        # Get the list of all validators
        validators = self.metagraph.get_validators(0)

        # Get the validator associated to the hotkey
        validator = next((x for x in validators if x[1] == caller), None)

        # Block hotkeys that are not an active validator hotkey
        if not validator:
            bt.logging.debug(
                f"Blacklisted a {synapse_type} request from a unrecognized hotkey {caller}"
            )
            return True, "Unrecognized hotkey"

        # Block hotkeys that do not have the latest version
        active_version = get_hyperparameter_value(
            self.subtensor, "weights_version", self.config.netuid
        )
        if caller_version < active_version:
            bt.logging.debug(
                f"Blacklisted a {synapse_type} request from a non-updated hotkey {caller}"
            )
            return True, "Non-updated hotkey"

        # Block hotkeys that do not have the minimum require stake to set weight
        weights_min_stake = get_weights_min_stake(self.subtensor.substrate)
        if validator[2] < weights_min_stake:
            bt.logging.debug(
                f"Blacklisted a {synapse_type} request from a not enought stake hotkey {caller}"
            )
            return True, "Not enough stake hotkey"

        bt.logging.trace(f"Not Blacklisting recognized hotkey {caller}")
        return False, "Hotkey recognized!"

    def _score(self, synapse: Score) -> Score:
        validator_uid = synapse.validator_uid

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

    def _blacklist_score(self, synapse: Score) -> typing.Tuple[bool, str]:
        return self._blacklist(synapse)

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

    def should_sync_metagraph(self):
        """
        True if the metagraph has been resynced, False otherwise.
        """
        last_updates = self.subtensor.substrate.query(
            module="SubtensorModule",
            storage_function="LastUpdate",
            params=[self.config.netuid],
        )
        if self.previous_last_updates == last_updates:
            return False

        # Save the new updates
        self.previous_last_updates = last_updates

        return True

    def update_firewall(self):
        # Get version and min stake
        version = get_hyperparameter_value(
            self.subtensor, "weights_version", self.config.netuid
        )
        weights_min_stake = get_weights_min_stake(self.subtensor.substrate)

        # Update the specifications
        specifications = {
            "neuron_version": version,
            "synapses": self.axon.forward_class_types,
        }
        bt.logging.debug(f"Firewall specifications {specifications}")

        # Define the valid validators
        validators = self.metagraph.get_validators(weights_min_stake)
        valid_validators = [x[1] for x in validators]

        # Update the firewall
        self.firewall.update(
            specifications=specifications,
            whitelist_hotkeys=valid_validators,
        )
        bt.logging.debug("Firewall updated")


def run_miner():
    """
    Main function to run the neuron.

    This function initializes and runs the neuron. It handles the main loop, state management, and interaction
    with the Bittensor network.
    """
    miner = None
    try:
        miner = Miner()
        miner.run_in_background_thread()

        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        bt.logging.info("Keyboard interrupt detected, exiting.")
        sys.exit(0)
    except Exception as e:
        bt.logging.error(traceback.format_exc())
        bt.logging.error(f"Unhandled exception: {e}")
        sys.exit(1)
    finally:
        if miner and miner.firewall:
            miner.firewall.stop()

        if miner and miner.file_monitor:
            miner.file_monitor.stop()

        if miner:
            bt.logging.info("Stopping axon")
            miner.axon.stop()


if __name__ == "__main__":
    run_miner()
