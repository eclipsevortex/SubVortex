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
from typing import List

from subvortex.validator.neuron.src.models.miner import Miner


def is_miner_suspicious(miner: Miner, suspicious_uids: List[int]):
    """
    True if the miner is in in the suspicious list, false otherwise
    the penalise factor will be returned too if there is one
    """
    return next(
        (
            (
                suspicious is not None,
                (suspicious.get("penalty_factor") if suspicious else None) or 0,
            )
            for suspicious in suspicious_uids
            if suspicious.get("uid") == miner.uid
            and suspicious.get("hotkey") == miner.hotkey
        ),
        (False, 0),
    )


def deregister_suspicious_uid(miners: List[Miner], moving_averaged_scores):
    """
    Deregister all miners that are either
    - suspicious from the load balancer
    - does not own their subtensor
    """
    for miner in miners:
        if not miner.suspicious:
            continue

        # Set the weight to 0 on the chain if there is no penalise factor
        # Set the weight to penalise factor if provided
        penalty_factor = miner.penalty_factor or 0
        moving_averaged_scores[miner.uid] = (
            moving_averaged_scores[miner.uid] * penalty_factor
        )
