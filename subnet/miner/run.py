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
import traceback
import bittensor.core.settings as btcs
import bittensor.utils.btlogging as btul
from substrateinterface import SubstrateInterface

from subnet.shared.checks import check_registration
from subnet.shared.utils import should_upgrade

from subnet.miner.version import VersionControl


def run(self):
    """
    Initiates and manages the main loop for the miner on the Bittensor network.

    This function performs the following primary tasks:
    1. Check for registration on the Bittensor network.
    2. Attaches the miner's forward, blacklist, and priority functions to its axon.
    3. Starts the miner's axon, making it active on the network.
    4. Regularly updates the metagraph with the latest network state.
    5. Optionally sets weights on the network, defining how much trust to assign to other nodes.
    6. Handles graceful shutdown on keyboard interrupts and logs unforeseen errors.

    The miner continues its operations until `should_exit` is set to True or an external interruption occurs.
    During each epoch of its operation, the miner waits for new blocks on the Bittensor network, updates its
    knowledge of the network (metagraph), and sets its weights. This process ensures the miner remains active
    and up-to-date with the network's latest state.

    Note:
        - The function leverages the global configurations set during the initialization of the miner.
        - The miner's axon serves as its interface to the Bittensor network, handling incoming and outgoing requests.

    Raises:
        KeyboardInterrupt: If the miner is stopped by a manual interruption.
        Exception: For unforeseen errors during the miner's operation, which are logged for diagnosis.
    """
    def initialize_substrate_interface():
        return SubstrateInterface(
            ss58_format=btcs.SS58_FORMAT,
            use_remote_preset=True,
            url=self.subtensor.chain_endpoint,
            type_registry=btcs.TYPE_REGISTRY,
        )

    def handler(obj, update_nr, subscription_id):
        try:
            current_block = obj["header"]["number"]
            btul.logging.debug(f"New block #{current_block}")
            btul.logging.debug(
                f"Blocks since epoch: {(current_block + netuid + 1) % (tempo + 1)}"
            )

            # --- Check to resync the metagraph.
            should_sync = self.should_sync_metagraph()
            btul.logging.debug(f"should_sync_metagraph() {should_sync}")
            if should_sync:
                self.metagraph.sync(subtensor=self.subtensor)
                btul.logging.info("Metagraph resynced")

                if self.firewall:
                    self.update_firewall()

            # --- Check for registration every 100 blocks (20 minutes).
            if current_block % 100 == 0:
                check_registration(self.subtensor, self.wallet, netuid)

            if should_upgrade(self.config.auto_update, self.last_upgrade_check):
                btul.logging.debug("Checking upgrade")
                must_restart = self.version_control.upgrade()
                if must_restart:
                    self.version_control.restart()
                    return

                self.last_upgrade_check = time.time()

            if self.should_exit:
                return True

        except Exception as e:
            btul.logging.error(f"Error in block handler: {e}")
            btul.logging.error(traceback.format_exc())
            return True

    netuid = self.config.netuid

    self.version_control = VersionControl()

    # Keep a track of last upgrade check
    self.last_upgrade_check = 0

    while not self.should_exit:
        try:
            # Initialize the SubstrateInterface
            block_handler_substrate = initialize_substrate_interface()

            # --- Check for registration.
            check_registration(self.subtensor, self.wallet, netuid)

            tempo = block_handler_substrate.query(
                module="SubtensorModule", storage_function="Tempo", params=[netuid]
            ).value

            # Subscribe to block headers
            block_handler_substrate.subscribe_block_headers(handler)

        except (BrokenPipeError, ConnectionError, TimeoutError) as e:
            btul.logging.error(f"[Subtensor] Connection error: {e}")
            btul.logging.error(traceback.format_exc())
            btul.logging.info("[Subtensor] Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            btul.logging.error(f"[Subtensor] Unhandled error: {e}")
            btul.logging.error(traceback.format_exc())
            break
