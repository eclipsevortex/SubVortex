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
import asyncio
import threading
import traceback
import bittensor.core.config as btcc
import bittensor.core.subtensor as btcs
import bittensor.utils.btlogging as btul
import bittensor.utils.networking as btun
import bittensor_wallet.wallet as btw
import bittensor_wallet.mock as btwm
from dotenv import load_dotenv

from subvortex.core.protocol import Score
from subvortex.core.shared.neuron import wait_until_registered
from subvortex.core.shared.substrate import get_weights_min_stake
from subvortex.core.shared.mock import MockSubtensor, MockAxon

from subvortex.core.core_bittensor.config.config_utils import update_config
from subvortex.core.core_bittensor.metagraph import SubVortexMetagraph
from subvortex.core.core_bittensor.axon import SubVortexAxon
from subvortex.core.core_bittensor.synapse import Synapse
from subvortex.core.core_bittensor.subtensor import (
    get_next_block,
    get_hyperparameter_value,
)

from subvortex.core.sse.sse_thread import SSEThread

from subvortex.core.file.file_monitor import FileMonitor
from subvortex.core.firewall.firewall_factory import (
    create_firewall_tool,
    create_firewall_observer,
)
from subvortex.miner.version import __version__ as THIS_VERSION
from subvortex.miner.neuron.src.firewall import Firewall
from subvortex.miner.neuron.src.config import (
    config,
    check_config,
    add_args,
)
from subvortex.miner.neuron.src.utils import load_request_log
from subvortex.miner.neuron.src.settings import Settings
from subvortex.miner.neuron.src.database import Database
from subvortex.miner.neuron.src.neuron import wait_until_no_multiple_occurrences

# Load the environment variables for the whole process
load_dotenv(override=True)


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

    async def run(self):
        # Display the settings
        btul.logging.info(f"Settings: {self.settings}")

        # Show miner version
        btul.logging.debug(f"Version {THIS_VERSION}")

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

        # Initialize the database
        btul.logging.info("loading database")
        self.database = Database(settings=self.settings)

        # Get the neuron
        self.neuron = await self.database.get_neuron(self.wallet.hotkey.ss58_address)
        btul.logging.debug(f"Miner based in {self.neuron.country}")

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

        # File monitor
        self.file_monitor = FileMonitor()
        self.file_monitor.start()

        # Start  starts the miner's axon, making it active on the network.
        btul.logging.info(f"Starting axon server on port: {self.config.axon.port}")
        self.axon.start()

        try:
            previous_last_update = None
            current_block = 0
            while True:
                try:
                    # Get the current block
                    current_block = get_next_block(
                        subtensor=self.subtensor, block=current_block
                    )
                    btul.logging.debug(f"Block #{current_block}")

                    # Check duplicate ips
                    btul.logging.debug("Checking ip occurrences...")
                    await wait_until_no_multiple_occurrences(
                        database=self.database, ip=self.neuron.ip
                    )

                    # Check registration
                    btul.logging.debug("Checking registration...")
                    await wait_until_registered(
                        database=self.database, hotkey=self.wallet.hotkey.ss58_address
                    )

                    # Get the last update of the neurons
                    last_updated = await self.database.get_neuron_last_updated()

                    # Check if the neurons have been updated
                    if previous_last_update != last_updated:
                        # At least one neuron has changed
                        btul.logging.debug(f"Neurons changed")

                        # Store the new last updated
                        previous_last_update = last_updated

                        # Update the current neuron
                        self.neuron = await self.database.get_neuron(
                            self.wallet.hotkey.ss58_address
                        )

                        # Update firewall if enabled
                        self.firewall and self.update_firewall()

                except Exception as ex:
                    btul.logging.error(f"Unhandled exception: {ex}")
                    btul.logging.debug(traceback.format_exc())

        except KeyboardInterrupt:
            btul.logging.info("Keyboard interrupt detected, exiting.")

        # Stop services
        self.sse and self.sse.stop()
        self.firewall and self.firewall.stop()
        self.file_monitor and self.file_monitor.stop()
        self.axon and self.axon.stop()

        # Stop loop events
        if not self.loop.is_closed():
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

        # Stop subtensor
        if hasattr(self, "subtensor"):
            btul.logging.debug("Closing subtensor connection")
            self.subtensor.close()

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


if __name__ == "__main__":
    asyncio.run(Miner().run())
