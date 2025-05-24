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
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw

import subvortex.core.core_bittensor.subtensor as scbs
from subvortex.core.version import to_spec_version
from subvortex.validator.version import __version__ as THIS_VERSION
from subvortex.validator.neuron.src.settings import Settings


def should_set_weights(
    settings: Settings, subtensor: btcs.Subtensor, uid: int, block: int
):
    # Get the weight rate limit
    weights_rate_limit = subtensor.weights_rate_limit(settings.netuid)
    btul.logging.debug(
        f"Weights rate limit: {weights_rate_limit}",
        prefix=settings.logging_name,
    )

    # Get the last update
    last_update = subtensor.get_hyperparameter(
        param_name="LastUpdate", netuid=settings.netuid
    )

    # Get the last time the validator set weights
    validator_last_update = last_update[uid] if uid < len(last_update) else 0
    btul.logging.debug(
        f"Last set weight at block #{validator_last_update}",
        prefix=settings.logging_name,
    )

    # Compute the next block to set weight
    # Have to add 1 block more otherwise you always have a failed attempt
    next_block = validator_last_update + (weights_rate_limit) + 1

    return next_block <= block


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
            version_key=to_spec_version(THIS_VERSION),
            max_retries=2,
        )

        if success:
            btul.logging.success(
                f"[green]Set weights on chain successfully![/green] ",
                prefix=settings.logging_name,
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
                prefix=settings.logging_name,
            )
            break

        btul.logging.warning(
            f"[orange]Set weights on chain failed[/orange]: Could not set weight on attempt {(settings.weights_setting_attempts - attempts) + 1}/{settings.weights_setting_attempts} - {message}",
            prefix=settings.logging_name,
        )

        # Check if there are still some retry or  not
        attempts = attempts - 1
        if attempts <= 0:
            # No more attempts available
            btul.logging.error(
                f":cross_mark: [red]Set weights on chain failed[/red]: Could not set weight after {settings.weights_setting_attempts} attempts",
                prefix=settings.logging_name,
            )
            break

        # Wait for the next block
        subtensor.wait_for_block()
