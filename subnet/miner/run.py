import time
import traceback
import bittensor as bt
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
            ss58_format=bt.__ss58_format__,
            use_remote_preset=True,
            url=self.subtensor.chain_endpoint,
            type_registry=bt.__type_registry__,
        )

    def handler(obj, update_nr, subscription_id):
        try:
            current_block = obj["header"]["number"]
            bt.logging.debug(f"New block #{current_block}")
            bt.logging.debug(
                f"Blocks since epoch: {(current_block + netuid + 1) % (tempo + 1)}"
            )

            # --- Check to resync the metagraph.
            should_sync = self.should_sync_metagraph()
            bt.logging.debug(f"should_sync_metagraph() {should_sync}")
            if should_sync:
                self.metagraph.sync(subtensor=self.subtensor)
                bt.logging.info("Metagraph resynced")

                if self.firewall:
                    self.update_firewall()

            # --- Check for registration every 100 blocks (20 minutes).
            if current_block % 100 == 0:
                check_registration(self.subtensor, self.wallet, netuid)

            if should_upgrade(self.config.auto_update, self.last_upgrade_check):
                bt.logging.debug("Checking upgrade")
                must_restart = self.version_control.upgrade()
                if must_restart:
                    self.version_control.restart()
                    return

                self.last_upgrade_check = time.time()

            if self.should_exit:
                return True

        except Exception as e:
            bt.logging.error(f"Error in block handler: {e}")
            bt.logging.error(traceback.format_exc())
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
            bt.logging.error(f"[Subtensor] Connection error: {e}")
            bt.logging.error(traceback.format_exc())
            bt.logging.info("[Subtensor] Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            bt.logging.error(f"[Subtensor] Unhandled error: {e}")
            bt.logging.error(traceback.format_exc())
            break
