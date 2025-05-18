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
import numpy as np
import bittensor.core.subtensor as btcs
import bittensor.core.metagraph as btcm
import bittensor.utils.weight_utils as btuw
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw

import subvortex.core.core_bittensor.subtensor as scbs
from subvortex.core.version import to_spec_version
from subvortex.core.shared.weights import set_weights
from subvortex.validator.version import __version__ as THIS_VERSION
from subvortex.validator.neuron.src.settings import Settings


async def should_set_weights(
    settings: Settings, subtensor: btcs.Subtensor, uid: int, block: int
):
    # Get the weight rate limit
    weights_rate_limit = await subtensor.weights_rate_limit(settings.netuid)
    btul.logging.debug(
        f"Weights rate limit: {weights_rate_limit}",
        prefix=settings.settings.logging_namer,
    )

    # Get the last update
    last_update = await subtensor.get_hyperparameter(
        param_name="LastUpdate", netuid=settings.netuid
    )

    # Get the last time the validator set weights
    validator_last_update = last_update[uid]
    btul.logging.debug(
        f"Last set weight at block #{validator_last_update}",
        prefix=settings.settings.logging_namer,
    )

    # Compute the next block to set weight
    # Have to add 1 block more otherwise you always have a failed attempt
    next_block = validator_last_update + (weights_rate_limit) + 1

    return next_block > block


def set_weights(
    settings: Settings,
    subtensor: "btcs.Subtensor",
    wallet: "btw.Wallet",
    uid: int,
    moving_scores: "np.NDArray",
):
    # Get the uids form teh moving scores array
    uids = np.arange(moving_scores.shape[0])

    # Process weights for the subnet
    uids_proceed, weights_proceed = scbs.process_weights_for_netuid(
        uids=uids,
        weights=moving_scores,
        netuid=settings.netuid,
        subtensor=subtensor,
    )

    success = False
    new_last_update = None
    attempts = settings.weights_setting_attempts
    while not success:
        # Get the last update for the validator
        last_update = subtensor.blocks_since_last_update(
            netuid=settings.netuid, uid=uid
        )

        # Set weights on the chain
        success, message = subtensor.set_weights(
            wallet=wallet,
            netuid=settings.netuid,
            uids=uids_proceed.tolist(),
            weights=weights_proceed.tolist(),
            wait_for_inclusion=True,
            wait_for_finalization=False,
            version_key=THIS_VERSION,
            max_retries=2,
        )

        if success:
            btul.logging.success(
                f"[green]Set weights on chain successfully![/green] ",
                prefix=settings.logging_namer,
            )
            break

        # Get the last update for the validator
        new_last_update = subtensor.blocks_since_last_update(
            netuid=settings.netuid, uid=uid
        )

        # Check if the last update has changed. If yes it means the weights have been set
        if new_last_update < last_update:
            success = True
            btul.logging.success(
                f"[green]Set weights on chain successfully![/green]",
                prefix=settings.logging_namer,
            )
            break

        btul.logging.warning(
            f"[orange]Set weights on chain failed[/orange]: Could not set weight on attempt {(settings.weights_setting_attempts - attempts) + 1}/{settings.weights_setting_attempts} - {message}",
            prefix=settings.logging_namer,
        )

        # Check if there are still some retry or  not
        attempts = attempts - 1
        if attempts < 0:
            # No more attempts available
            btul.logging.error(
                f":cross_mark: [red]Set weights on chain failed[/red]: Could not set weight after {settings.weights_setting_attempts} attempts",
                prefix=settings.logging_namer,
            )
            break

        # Wait for the next block
        subtensor.wait_for_block()


def set_weights2(
    uid: int,
    subtensor: "btcs.Subtensor",
    wallet: "btw.Wallet",
    netuid: int,
    metagraph: "btcm.Metagraph",
    moving_averaged_scores: "np.NDArray",
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
        uids (np.NDArray): miners UIDs on the network.
        metagraph (btul.metagraph): Bittensor metagraph.
        moving_averaged_scores (np.NDArray): .
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
    nan_idxs = np.isnan(moving_averaged_scores)
    moving_averaged_scores_no_nan = np.where(
        nan_idxs,
        np.zeros_like(moving_averaged_scores),
        moving_averaged_scores,
    )

    # Gather negative indices
    neg_idxs = np.where(moving_averaged_scores_no_nan < 0)

    # Ensure positive by shifting scores
    minimum = np.min(moving_averaged_scores_no_nan)

    # Replace NaNs with the minimum value
    moving_averaged_scores_no_nan[nan_idxs] = minimum

    # Make all values positive
    if minimum < 0:
        positive_moving_averaged_scores = moving_averaged_scores_no_nan - minimum
    else:
        positive_moving_averaged_scores = moving_averaged_scores_no_nan
    btul.logging.debug(f"Positive scores: {positive_moving_averaged_scores}")

    # Push originally negative indices to zero
    positive_moving_averaged_scores[neg_idxs] = 0

    # Normalize the scores
    sum_scores = np.sum(positive_moving_averaged_scores)
    btul.logging.info(f"Score sum: {sum_scores}")
    if sum_scores > 0:
        raw_weights = positive_moving_averaged_scores / sum_scores
    else:
        raw_weights = np.zeros_like(positive_moving_averaged_scores)

    # Ensure no NaNs in raw_weights
    raw_weights = np.where(
        np.isnan(raw_weights),
        np.zeros_like(raw_weights),
        raw_weights,
    )

    btul.logging.debug("raw_weights", raw_weights)
    btul.logging.debug("raw_weight_uids", metagraph.uids)

    # Process the raw weights to final_weights via subtensor limitations
    (
        processed_weight_uids,
        processed_weights,
    ) = btuw.process_weights_for_netuid(
        uids=metagraph.uids,
        weights=raw_weights,
        netuid=settings.netuid,
        subtensor=subtensor,
        metagraph=metagraph,
    )
    btul.logging.debug("processed_weights", processed_weights)
    btul.logging.debug("processed_weight_uids", processed_weight_uids)

    # Convert to uint16 weights and uids
    uint_uids, uint_weights = btuw.convert_weights_and_uids_for_emit(
        uids=processed_weight_uids, weights=processed_weights
    )
    btul.logging.debug("uint_weights", uint_weights)
    btul.logging.debug("uint_uids", uint_uids)

    # Set the weights on chain via our subtensor connection
    success, message = set_weights(
        uid=uid,
        subtensor=subtensor,
        wallet=wallet,
        netuid=settings.netuid,
        uids=uint_uids,
        weights=uint_weights,
        version_key=to_spec_version(THIS_VERSION),
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
