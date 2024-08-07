import bittensor as bt
from typing import List

from subnet import protocol
from subnet.constants import DEFAULT_PROCESS_TIME
from subnet.validator.models import Miner


async def send_scope(self, miner: Miner):
    """
    Send the scope synapse to the miner and return the version
    """
    try:
        # Send the score details to the miner
        response: List[protocol.Score] = await self.dendrite(
            axons=[self.metagraph.axons[miner.uid]],
            synapse=protocol.Score(
                validator_uid=self.uid,
                count=miner.ip_occurences,
                availability=miner.availability_score,
                latency=miner.latency_score,
                reliability=miner.reliability_score,
                distribution=miner.distribution_score,
                score=miner.score,
            ),
            deserialize=True,
            timeout=DEFAULT_PROCESS_TIME,
        )

        version = response[0] if len(response) > 0 else None
        return version or "0.0.0"
    except Exception as err:
        bt.logging.warning(f"[{miner.uid}] send_scope() Sending scope failed: {err}")

    return "0.0.0"
