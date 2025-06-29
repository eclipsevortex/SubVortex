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
import bittensor.utils.btlogging as btul
from typing import List

from subvortex.core import protocol
from subvortex.core.constants import DEFAULT_PROCESS_TIME
from subvortex.validator.neuron.src.models.miner import Miner


async def send_scope(self, miner: Miner, ip_occurences: int, block: int, reason: str, detail: str, moving_score: float):
    """
    Send the scope synapse to the miner and return the version
    """
    try:
        # Send the score details to the miner
        response: List[protocol.Score] = await self.dendrite(
            axons=[miner.axon],
            synapse=protocol.Score(
                validator_uid=self.neuron.uid,
                rank=miner.rank,
                count=ip_occurences,
                availability=miner.availability_score,
                latency=miner.latency_score,
                reliability=miner.reliability_score,
                distribution=miner.distribution_score,
                score=miner.score,
                moving_score=moving_score,
                penalty_factor=miner.penalty_factor if miner.suspicious else None,
                block=block,
                reason=reason,
                detail=detail,
            ),
            deserialize=True,
            timeout=DEFAULT_PROCESS_TIME,
        )

        version = response[0] if len(response) > 0 else None
        return version or "0.0.0"
    except Exception as err:
        btul.logging.warning(f"[{miner.uid}] send_scope() Sending scope failed: {err}")

    return "0.0.0"
