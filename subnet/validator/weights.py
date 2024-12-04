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
import torch
import bittensor.core.subtensor as btcs
import bittensor.core.metagraph as btcm
import bittensor.utils.weight_utils as btuw
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw

from subnet import __spec_version__ as spec_version
from subnet.shared.weights import set_weights


def set_weights_for_validator(
    uid: int,
    device: torch.device,
    subtensor: "btcs.Subtensor",
    wallet: "btw.Wallet",
    netuid: int,
    metagraph: "btcm.Metagraph",
    moving_averaged_scores: "torch.Tensor",
    wait_for_inclusion: bool = True,
    wait_for_finalization: bool = False,
):
    """
    Sets miners' weights on the Bittensor network.

    This function assigns a weight of 1 to the current miner (identified by its UID) and
    a weight of 0 to all other peers in the network. The weights determine the trust level
    the miner assigns to other nodes on the network.

    Args:
        subtensor (btcs.subtensor): The Bittensor object managing the blockchain connection.
        wallet (btw.wallet): The miner's wallet holding cryptographic information.
        netuid (int): The unique identifier for the chain subnet.
        uids (torch.Tensor): miners UIDs on the network.
        metagraph (btul.metagraph): Bittensor metagraph.
        moving_averaged_scores (torch.Tensor): .
        tempo (int): Tempo for 'netuid' subnet.
        wait_for_inclusion (bool, optional): Wether to wait for the extrinsic to enter a block
        wait_for_finalization (bool, optional): Wether to wait for the extrinsic to be finalized on the chain

    Returns:
        success (bool):
            flag is true if extrinsic was finalized or uncluded in the block.
            If we did not wait for finalization / inclusion, the response is true.

    Raises:
        Exception: If there's an error while setting weights, the exception is logged for diagnosis.
    """
    # Calculate the average reward for each uid across non-zero values.

    # Replace any NaN values with 0
    nan_idxs = torch.where(torch.isnan(moving_averaged_scores))[0]
    moving_averaged_scores_no_nan = torch.where(
        torch.isnan(moving_averaged_scores),
        torch.zeros_like(moving_averaged_scores),
        moving_averaged_scores,
    )

    # Gather negative indices
    neg_idxs = torch.where(moving_averaged_scores_no_nan < 0)[0]

    # Ensure positive
    minimum = min(moving_averaged_scores_no_nan)

    # Replace nan with min
    moving_averaged_scores_no_nan[nan_idxs] = minimum.clone()

    # Make all values positive
    if minimum < 0:
        positive_moving_averaged_scores = moving_averaged_scores_no_nan - minimum
    else:
        positive_moving_averaged_scores = moving_averaged_scores_no_nan
    btul.logging.debug(f"Positive scores", positive_moving_averaged_scores)

    # Push all orinally negative indices to zero
    positive_moving_averaged_scores[neg_idxs] = 0

    # Normalize, ensuring no division by zero or NaNs occur
    sum_scores = positive_moving_averaged_scores.sum()
    btul.logging.info(f"Score sum: {sum_scores}")
    if sum_scores > 0:
        raw_weights = torch.nn.functional.normalize(
            positive_moving_averaged_scores, p=1, dim=0
        )
    else:
        raw_weights = torch.zeros_like(positive_moving_averaged_scores)

    # Doubly ensure raw_weights does not contain NaNs (this should not happen after normalization, but as an extra precaution)
    raw_weights = torch.where(
        torch.isnan(raw_weights),
        torch.zeros_like(raw_weights),
        raw_weights,
    )

    btul.logging.debug("raw_weights", raw_weights)
    btul.logging.debug("raw_weight_uids", metagraph.uids)

    # Process the raw weights to final_weights via subtensor limitations.
    (
        processed_weight_uids,
        processed_weights,
    ) = btuw.process_weights_for_netuid(
        uids=metagraph.uids.to(device),
        weights=raw_weights,
        netuid=netuid,
        subtensor=subtensor,
        metagraph=metagraph,
    )
    btul.logging.debug("processed_weights", processed_weights)
    btul.logging.debug("processed_weight_uids", processed_weight_uids)

    # Convert to uint16 weights and uids.
    uint_uids, uint_weights = btuw.convert_weights_and_uids_for_emit(
        uids=processed_weight_uids, weights=processed_weights
    )
    btul.logging.debug("uint_weights", uint_weights)
    btul.logging.debug("uint_uids", uint_uids)

    # Set the weights on chain via our subtensor connection.
    success, message = set_weights(
        uid=uid,
        subtensor=subtensor,
        wallet=wallet,
        netuid=netuid,
        uids=uint_uids,
        weights=uint_weights,
        version_key=spec_version,
        wait_for_inclusion=wait_for_inclusion,
        wait_for_finalization=wait_for_finalization,
    )

    if success is True:
        btul.logging.success(f"[green]Set weights on chain successfully![/green] ")
    else:
        btul.logging.error(
            f":cross_mark: [red]Set weights on chain failed[/red]: {message}"
        )

    return success, message, uint_weights
