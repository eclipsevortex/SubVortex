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
import bittensor.core.subtensor as btcs
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw
from torch import Tensor
from typing import Tuple

from subnet.shared.substrate import get_weights_min_stake


def should_wait_to_set_weights(current_block, last_epoch_block, tempo):
    diff_blocks = current_block - last_epoch_block
    return diff_blocks <= tempo


def should_set_weights(
    self,
    current_block,
    prev_step_block,
    tempo,
    disable_set_weights: bool = False,
) -> bool:
    # Check if the validator just started
    if self.step == 0:
        return False

    # Check if enough epoch blocks have elapsed since the last epoch.
    if disable_set_weights:
        return False

    # Check validator has enough state to set weight
    validator_stake = self.metagraph.S[self.uid]
    weight_min_stake = get_weights_min_stake(self.subtensor.substrate)
    has_enough_stake = validator_stake >= weight_min_stake
    if has_enough_stake == False:
        btul.logging.warning(
            f"Not enough stake t{validator_stake} to set weight, require a minimum of t{weight_min_stake}. Please stake more if you do not want to be de-registered!"
        )
        return False

    return not should_wait_to_set_weights(current_block, prev_step_block, tempo)


def set_weights(
    subtensor: "btcs.Subtensor",
    wallet: "btw.Wallet",
    netuid: int,
    uids: "Tensor",
    weights: "Tensor",
    version_key: int,
    wait_for_inclusion: bool = False,
    wait_for_finalization: bool = False,
) -> Tuple[bool, str]:
    """
    Sets the miner's weights on the Bittensor network.

    This function assigns a weight of 1 to the current miner (identified by its UID) and
    a weight of 0 to all other peers in the network. The weights determine the trust level
    the miner assigns to other nodes on the network.

    The function performs the following steps:
    1. Queries the Bittensor network for the total number of peers.
    2. Sets a weight vector with a value of 1 for the current miner and 0 for all other peers.
    3. Updates these weights on the Bittensor network using the `set_weights` method of the subtensor.
    4. Optionally logs the weight-setting operation to Weights & Biases (wandb) for monitoring.

    Args:
        subtensor (btcs.Subtensor): The Bittensor object managing the blockchain connection.
        wallet (btw.Wallet): The miner's wallet holding cryptographic information.
        netuid (int): The unique identifier for the chain subnet.
        uids (torch.Tensor): miners UIDs on the network.
        weights (torch.Tensor): weights to sent for UIDs on the network.
        metagraph (btcm.Metagraph): Bittensor metagraph.
        wandb_on (bool, optional): Flag to determine if logging to Weights & Biases is enabled. Defaults to False.
        wait_for_inclusion (bool, optional): Wether to wait for the extrinsic to enter a block.
        wait_for_finalization (bool, optional): Wether to wait for the extrinsic to be finalized on the chain.

    Returns:
        success (bool):
            flag is true if extrinsic was finalized or uncluded in the block.
            If we did not wait for finalization / inclusion, the response is true.
        message (str):
            message returned by the chain.

    Raises:
        Exception: If there's an error while setting weights, the exception is logged for diagnosis.
    """
    try:
        # --- Set weights.
        success, message = subtensor.set_weights(
            wallet=wallet,
            netuid=netuid,
            uids=uids,
            weights=weights,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
            version_key=version_key,
        )

        return success, message
    except Exception as e:
        btul.logging.error(f"Failed to set weights on chain with exception: { e }")
        return False, message
