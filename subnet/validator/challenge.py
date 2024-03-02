import torch
import time
import asyncio
import bittensor as bt

from subnet import protocol
from subnet.constants import (
    AVAILABILITY_FAILURE_REWARD,
    LATENCY_FAILURE_REWARD,
    DISTRIBUTION_FAILURE_REWARD,
    AVAILABILITY_WEIGHT,
    LATENCY_WEIGHT,
    RELIABILLITY_WEIGHT,
    DISTRIBUTION_WEIGHT,
)
from subnet.shared.subtensor import get_current_block
from subnet.validator.utils import get_available_query_miners
from subnet.validator.localisation import get_country
from subnet.validator.bonding import update_statistics
from subnet.validator.score import (
    compute_reliability_score,
    compute_latency_score,
    compute_distribution_score,
)


CHALLENGE_NAME = "Challenge"


async def handle_synapse(self, uid: int, axon: bt.AxonInfo):
    # TODO: Use that response so check availability? It is the VPS and reliability can
    # be tested by the websocket?
    # response = await self.dendrite(
    #     axons=[self.metagraph.axons[uid]],
    #     synapse=protocol.Subtensor(),
    #     deserialize=True,
    #     timeout=5,
    # )

    # Get the subtensor ip
    ip = axon.ip
    if ip == '0.0.0.0':
        bt.logging.warning(f"[{CHALLENGE_NAME}][{uid}] Axon ip is not povided")
        return False, None, None

    # Get the country of the subtensor via a free api
    country = get_country(ip)
    bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Subtensor country {country}")

    process_time = None
    try:
        # Create a subtensor with the ip return by the synapse
        config = bt.subtensor.config()
        config.subtensor.network = "local"
        config.subtensor.chain_endpoint = f"ws://{ip}:9944"
        miner_subtensor = bt.subtensor(config)

        # Start the timer
        start_time = time.time()

        # Get the current block from the miner subtensor
        miner_block = miner_subtensor.get_current_block()

        # Compute the process time
        process_time = time.time() - start_time

        # Get the current block from the validator subtensor
        validator_block = get_current_block(self.subtensor)

        # Check both blocks are the same
        verified = miner_block == validator_block
    except Exception:
        verified = False

    return verified, country, process_time


async def challenge_data(self):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Execute the challenge
    tasks = []
    responses = []
    for idx, (uid) in enumerate(uids):
        axon = self.metagraph.axons[idx]

        tasks.append(asyncio.create_task(handle_synapse(self, uid, axon)))
        responses = await asyncio.gather(*tasks)

    # Compute the score
    rewards: torch.FloatTensor = torch.zeros(len(responses), dtype=torch.float32).to(
        self.device
    )
    for idx, (uid, (verified)) in enumerate(zip(uids, responses)):
        # Get axon
        axon = self.metagraph.axons[idx]

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Update statistics
        await update_statistics(
            ss58_address=hotkey,
            success=verified,
            task_type="challenge",
            database=self.database,
        )

        # Compute score for availability
        availability_score = 1.0 if verified else AVAILABILITY_FAILURE_REWARD
        bt.logging.debug(
            f"[{CHALLENGE_NAME}][{uid}] Availability score {availability_score}"
        )

        # Compute score for latency
        latency_score = (
            compute_latency_score(idx, self.country, responses)
            if verified
            else LATENCY_FAILURE_REWARD
        )
        bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Latency score {latency_score}")

        # Compute score for reliability
        reliability_score = await compute_reliability_score(self.database, hotkey)
        bt.logging.debug(
            f"[{CHALLENGE_NAME}][{uid}] Reliability score {reliability_score}"
        )

        # Compute score for distribution
        distribution_score = (
            compute_distribution_score(idx, responses)
            if responses[idx][2] is not None
            else DISTRIBUTION_FAILURE_REWARD
        )
        bt.logging.debug(
            f"[{CHALLENGE_NAME}][{uid}] Distribution score {distribution_score}"
        )

        # Compute final score
        rewards[idx] = (
            (AVAILABILITY_WEIGHT * availability_score)
            + (LATENCY_WEIGHT * latency_score)
            + (RELIABILLITY_WEIGHT * reliability_score)
            + (DISTRIBUTION_WEIGHT * distribution_score)
        ) / 4.0
        bt.logging.info(f"[{CHALLENGE_NAME}][{uid}] Final score {rewards[idx]}")



    # Compute forward pass rewards
    scattered_rewards: torch.FloatTensor = (
        self.moving_averaged_scores.to(self.device)
        .scatter(
            0,
            torch.tensor(uids).to(self.device),
            rewards.to(self.device),
        )
        .to(self.device)
    )
    bt.logging.trace(f"Scattered rewards: {scattered_rewards}")

    # Update moving_averaged_scores with rewards produced by this step.
    # TODO: issue here as the types does not allow multiplication
    alpha: float = 0.05
    self.moving_averaged_scores = alpha * scattered_rewards + (
        1 - alpha
    ) * self.moving_averaged_scores.to(self.device)
    bt.logging.trace(f"Updated moving avg scores: {self.moving_averaged_scores}")

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")
