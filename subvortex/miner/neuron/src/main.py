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
import os
import sys
import time
import copy
import typing
import asyncio
import threading
import traceback
import bittensor.core.config as btcc
import bittensor.core.subtensor as btcs
import bittensor.utils.btlogging as btul
import bittensor.utils.networking as btun
import bittensor_wallet.wallet as btw
import bittensor_wallet.mock as btwm

from subvortex.core.protocol import Score
from subvortex.core.shared.checks import check_registration
from subvortex.core.shared.subtensor import get_hyperparameter_value
from subvortex.core.shared.substrate import get_weights_min_stake
from subvortex.core.shared.mock import MockMetagraph, MockSubtensor, MockAxon

from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.metagraph import SubVortexMetagraph
from subvortex.core.core_bittensor.axon import SubVortexAxon
from subvortex.core.core_bittensor.synapse import Synapse

from subvortex.core.sse.sse_thread import SSEThread

from subvortex.core.file.file_monitor import FileMonitor
from subvortex.core.firewall.firewall_factory import (
    create_firewall_tool,
    create_firewall_observer,
)
from subvortex.miner.version import __version__ as THIS_VERSION
from subvortex.miner.core.run import run
from subvortex.miner.core.firewall import Firewall
from subvortex.miner.core.config import (
    config,
    check_config,
    add_args,
)
from subvortex.miner.core.utils import load_request_log
from subvortex.miner.metagraph.src.settings import Settings


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

    subtensor: "btcs.Subtensor"
    wallet: "btw.Wallet"
    metagraph: SubVortexMetagraph

    def __init__(self, config=None):
        self.config = Miner.config()
        self.check_config(self.config)

        # Create settings
        settings = Settings.create()
        update_config(settings, config)

        btul.logging(
            config=self.config,
            logging_dir=self.config.miner.full_path,
            debug=True,
        )
        btul.logging.set_trace(self.config.logging.trace)
        btul.logging._stream_formatter.set_trace(self.config.logging.trace)
        btul.logging.info(f"{self.config}")

        # Show the pid
        pid = os.getpid()
        btul.logging.debug(f"miner PID: {pid}")

        # Show miner version
        btul.logging.debug(f"miner version {THIS_VERSION}")

        # File monitor
        self.file_monitor = FileMonitor()
        self.file_monitor.start()

        # Server-Sent Events
        self.sse = SSEThread(ip=self.config.sse.firewall.ip, port=self.config.sse.port)
        self.sse.server.add_stream("firewall")
        self.sse.start()

        # Firewall
        self.firewall = None
        if self.config.firewall.on:
            btul.logging.debug(
                f"Starting firewall on interface {self.config.firewall.interface}"
            )
            port = (
                self.config.axon.external_port
                if self.config.axon.external_port is not None
                else self.config.axon.port
            )
            self.firewall = Firewall(
                observer=create_firewall_observer(),
                tool=create_firewall_tool(),
                sse=self.sse.server,
                port=port,
                interface=self.config.firewall.interface,
                config_file=self.config.firewall.config,
            )
            self.file_monitor.add_file_provider(self.firewall.provider)
            self.firewall.start()

        # Init wallet.
        btul.logging.debug("loading wallet")
        self.wallet = (
            btwm.MockWallet(config=self.config)
            if self.config.mock
            else btw.Wallet(config=self.config)
        )
        self.wallet.create_if_non_existent()
        btul.logging.debug(f"wallet: {str(self.wallet)}")

        # Init subtensor
        btul.logging.debug("loading subtensor")
        self.subtensor = (
            MockSubtensor(self.config.netuid, wallet=self.wallet)
            if self.config.miner.mock_subtensor
            else btcs.Subtensor(config=self.config, network="local")
        )
        btul.logging.debug(str(self.subtensor))
        self.current_block = self.subtensor.get_current_block()

        btul.logging.debug("checking wallet registration")
        check_registration(self.subtensor, self.wallet, self.config.netuid)

        # Init metagraph.
        btul.logging.debug("loading metagraph")
        self.metagraph = (
            MockMetagraph(self.config.netuid, subtensor=self.subtensor)
            if self.config.mock
            else SubVortexMetagraph(
                netuid=self.config.netuid, network=self.subtensor.network, sync=False
            )
        )

        self.metagraph.sync(subtensor=self.subtensor)  # Sync metagraph with subtensor.
        btul.logging.debug(str(self.metagraph))

        self.uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        btul.logging.info(f"Running miner on uid: {self.uid}")

        # The axon handles request processing, allowing validators to send this process requests.
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
        btul.logging.info(f"Axon {self.axon}")
        btul.logging.info(f"Axon version {self.axon.info().version}")

        # Attach determiners which functions are called when servicing a request.
        btul.logging.info("Attaching forward functions to axon.")
        self.axon.attach(
            forward_fn=self._score,
            blacklist_fn=self._blacklist_score,
        )

        # Serve passes the axon information to the network + netuid we are hosting on.
        # This will auto-update if the axon port of external ip have changed.
        btul.logging.info(
            f"Serving axon {self.axon} on network: {self.subtensor.chain_endpoint} with netuid: {self.config.netuid}"
        )
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)

        # Check there is not another miner running on the machine
        btul.logging.debug(f"Checking number of miners on same ip")
        number_of_miners = len(
            [axon for axon in self.metagraph.axons if self.axon.external_ip == axon.ip]
        )
        if number_of_miners > 1:
            btul.logging.error(
                "At least one miner is already running on this machine. If you run more than one miner you will penalise all of your miners until you get de-registered or start each miner on a unique machine"
            )
            sys.exit(1)

        # File monitor
        self.file_monitor = FileMonitor()
        self.file_monitor.start()

        # Start  starts the miner's axon, making it active on the network.
        btul.logging.info(f"Starting axon server on port: {self.config.axon.port}")
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
            btul.logging.debug(
                f"Blacklisted a {synapse_type} request from a unrecognized hotkey {caller}"
            )
            return True, "Unrecognized hotkey"

        # Block hotkeys that do not have the latest version
        hyperparameters = self.subtensor.get_subnet_hyperparameters(self.config.netuid)
        if caller_version < hyperparameters.weights_version:
            btul.logging.debug(
                f"Blacklisted a {synapse_type} request from a non-updated hotkey {caller}"
            )
            return True, "Non-updated hotkey"

        # Block hotkeys that do not have the minimum require stake to set weight
        weights_min_stake = get_weights_min_stake(self.subtensor.substrate)
        if validator[2] < weights_min_stake:
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
            btul.logging.debug("Starting miner in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            btul.logging.debug("Started")

    def stop_run_thread(self):
        """
        Stops the miner's operations that are running in the background thread.
        """
        if self.is_running:
            btul.logging.debug("Stopping miner in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            btul.logging.debug("Stopped")

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
            "hotkey": self.wallet.hotkey.ss58_address,
        }
        btul.logging.debug(f"Firewall specifications {specifications}")

        # Define the valid validators
        validators = self.metagraph.get_validators(weights_min_stake)
        valid_validators = [x[1] for x in validators]

        # Update the firewall
        self.firewall.update(
            specifications=specifications,
            whitelist_hotkeys=valid_validators,
        )
        btul.logging.debug("Firewall updated")


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
        btul.logging.info("Keyboard interrupt detected, exiting.")
        sys.exit(0)
    except Exception as e:
        btul.logging.error(traceback.format_exc())
        btul.logging.error(f"Unhandled exception: {e}")
        sys.exit(1)
    finally:
        if miner and miner.sse:
            miner.sse.stop()

        if miner and miner.firewall:
            miner.firewall.stop()

        if miner and miner.file_monitor:
            miner.file_monitor.stop()

        if miner:
            btul.logging.info("Stopping axon")
            miner.axon.stop()


if __name__ == "__main__":
    run_miner()
