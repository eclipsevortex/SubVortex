import wandb
import torch
import time
import asyncio
import bittensor as bt
import random

from subnet import protocol
from subnet.constants import (
    AVAILABILITY_FAILURE_REWARD,
    LATENCY_FAILURE_REWARD,
    DISTRIBUTION_FAILURE_REWARD,
    RELIABILLITY_WEIGHT_FAILURE_REWARD,
    AVAILABILITY_WEIGHT,
    LATENCY_WEIGHT,
    RELIABILLITY_WEIGHT,
    DISTRIBUTION_WEIGHT,
)
from subnet.shared.subtensor import get_current_block
from subnet.validator.event import EventSchema
from subnet.validator.utils import ping_and_retry_uids, get_next_uids, ping_uid
from subnet.validator.localisation import get_country
from subnet.validator.bonding import update_statistics
from subnet.validator.state import log_event
from subnet.validator.database import build_miners_table
from subnet.validator.score import (
    compute_reliability_score,
    compute_latency_score,
    compute_distribution_score,
)
from substrateinterface.base import SubstrateInterface


CHALLENGE_NAME = "Challenge"
DEFAULT_PROCESS_TIME = 5


async def check_miner_availability(self, uid: int):
    # Check the miner
    availble = False

    try:
        # Ping the miner - miner and subtensor are unique so we consider a failure if one or the other is not reachable
        availble = await ping_uid(self, uid)
    except Exception:
        availble = False

    return availble


async def handle_synapse(self, uid: int):
    # Get miner ip
    ip = self.metagraph.axons[uid].ip

    # Get the country of the subtensor via a free api
    country = get_country(ip)
    bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Subtensor country {country}")

    # Check miner is available
    available = await check_miner_availability(self, uid)
    if available == False:
        bt.logging.warning(f"[{CHALLENGE_NAME}][{uid}] Miner is not reachable")
        return available, country, DEFAULT_PROCESS_TIME

    # Check the subtensor is available
    process_time = None
    try:
        # Create a subtensor with the ip return by the synapse
        substrate = SubstrateInterface(
            ss58_format=bt.__ss58_format__,
            use_remote_preset=True,
            url=f"ws://{ip}:9944",
            type_registry=bt.__type_registry__,
        )

        # Start the timer
        start_time = time.time()

        # Get the current block from the miner subtensor
        miner_block = substrate.get_block()
        if miner_block != None:
            miner_block = miner_block["header"]["number"]

        # Compute the process time
        process_time = time.time() - start_time

        # Get the current block from the validator subtensor
        validator_block = get_current_block(self.subtensor)

        # Check blocks and miner availability
        verified = miner_block == validator_block or miner_block is not None

        bt.logging.trace(
            f"[{CHALLENGE_NAME}][{uid}] Verified ? {verified} - val: {validator_block}, miner:{miner_block}"
        )
    except Exception:
        verified = False
        process_time = DEFAULT_PROCESS_TIME if process_time is None else process_time
        bt.logging.warning(f"[{CHALLENGE_NAME}][{uid}] Subtensor not verified")

    return verified, country, process_time


async def challenge_data(self):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    event = EventSchema(
        completion_times=[],
        availability_scores=[],
        latency_scores=[],
        reliability_scores=[],
        distribution_scores=[],
        moving_averaged_scores=[],
        block=self.subtensor.get_current_block(),
        uids=[],
        step_length=0.0,
        best_uid=-1,
        best_hotkey="",
        rewards=[],
    )

    # Select the miners
    validator_hotkey = self.metagraph.hotkeys[self.uid]
    uids = await get_next_uids(self, validator_hotkey, k=10)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Initialise the rewards object
    rewards: torch.FloatTensor = torch.zeros(len(uids), dtype=torch.float32).to(
        self.device
    )

    # Execute the challenge
    tasks = []
    responses = []
    for idx, (uid) in enumerate(uids):
        tasks.append(asyncio.create_task(handle_synapse(self, uid)))
        responses = await asyncio.gather(*tasks)

    # Init wandb table data
    availability_scores = []
    latency_scores = []
    reliability_scores = []
    distribution_scores = []

    bt.logging.warning(f"[{CHALLENGE_NAME}] Computing uids scores")

    # Compute the score
    for idx, (uid, (verified, country, process_time)) in enumerate(
        zip(uids, responses)
    ):
        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Initialise scores
        availability_score = 0
        latency_score = 0
        reliability_score = 0
        distribution_score = 0

        # Check # of miners per IP - Only one miner per IP is allowed
        ip = self.metagraph.axons[uid].ip
        miners_on_ip = [
            self.metagraph.axons[uid].ip
            for uid in uids
            if self.metagraph.axons[uid].ip == ip
        ]
        number_of_miners = len(miners_on_ip)
        if number_of_miners == 1:
            # Compute the scores if only one miner is running on the axon machine

            # Compute score for availability
            availability_score = (
                1.0 if verified and number_of_miners else AVAILABILITY_FAILURE_REWARD
            )
            availability_scores.append(availability_score)
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{uid}] Availability score {availability_score}"
            )

            # Compute score for latency
            latency_score = (
                compute_latency_score(idx, uid, self.country, responses)
                if verified
                else LATENCY_FAILURE_REWARD
            )
            latency_scores.append(latency_score)
            bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Latency score {latency_score}")

            # Compute score for reliability
            reliability_score = (
                await compute_reliability_score(uid, self.database, hotkey)
                if verified
                else RELIABILLITY_WEIGHT_FAILURE_REWARD
            )
            reliability_scores.append(reliability_score)
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{uid}] Reliability score {reliability_score}"
            )

            # Compute score for distribution
            distribution_score = (
                compute_distribution_score(idx, responses)
                if verified and responses[idx][2] is not None
                else DISTRIBUTION_FAILURE_REWARD
            )
            distribution_scores.append((uid, distribution_score))
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{uid}] Distribution score {distribution_score}"
            )

            # Compute final score
            rewards[idx] = (
                (AVAILABILITY_WEIGHT * availability_score)
                + (LATENCY_WEIGHT * latency_score)
                + (RELIABILLITY_WEIGHT * reliability_score)
                + (DISTRIBUTION_WEIGHT * distribution_score)
            ) / (
                AVAILABILITY_WEIGHT
                + LATENCY_WEIGHT
                + RELIABILLITY_WEIGHT
                + DISTRIBUTION_WEIGHT
            )
        else:
            # More than 1 miner running in the axon machine
            # Someone is trying to hack => Penalize all the miners on the axon machine
            rewards[idx] = 0
            bt.logging.warning(
                f"[{CHALLENGE_NAME}][{uid}] Number of miners on same IP {number_of_miners}"
            )

        bt.logging.info(f"[{CHALLENGE_NAME}][{uid}] Final score {rewards[idx]}")

        # Send the score details to the miner
        response = await self.dendrite(
            axons=[self.metagraph.axons[uid]],
            synapse=protocol.Score(
                validator_uid=self.uid,
                count=number_of_miners,
                availability=availability_score,
                latency=latency_score,
                reliability=reliability_score,
                distribution=distribution_score,
                score=rewards[idx],
            ),
            deserialize=True,
            timeout=5,
        )

        # Update statistics
        await update_statistics(
            ss58_address=hotkey,
            success=verified,
            uid=uid,
            country=country,
            version=response[0],
            reward=rewards[idx].item(),
            availability_score=availability_score,
            latency_score=latency_score,
            reliability_score=reliability_score,
            distribution_score=distribution_score,
            database=self.database,
        )

        # Log the event data for this specific challenge
        event.uids.append(uid)
        event.completion_times.append(process_time)
        event.rewards.append(rewards[idx].item())
        event.availability_scores.append(availability_score)
        event.latency_scores.append(latency_score)
        event.reliability_scores.append(reliability_score)
        event.distribution_scores.append(distribution_score)

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
    bt.logging.trace(f"[{CHALLENGE_NAME}] Scattered rewards: {scattered_rewards}")

    # Update moving_averaged_scores with rewards produced by this step.
    # alpha of 0.2 means that each new score replaces 20% of the weight of the previous weights
    alpha: float = 0.2
    self.moving_averaged_scores = alpha * scattered_rewards + (
        1 - alpha
    ) * self.moving_averaged_scores.to(self.device)
    event.moving_averaged_scores = self.moving_averaged_scores.tolist()
    bt.logging.trace(
        f"[{CHALLENGE_NAME}] Updated moving avg scores: {self.moving_averaged_scores}"
    )

    # Display step time in seconds
    forward_time = time.time() - start_time
    event.step_length = forward_time
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")

    # Determine the best UID based on rewards
    if event.rewards:
        best_index = max(range(len(event.rewards)), key=event.rewards.__getitem__)
        event.best_uid = event.uids[best_index]
        event.best_hotkey = self.metagraph.hotkeys[event.best_uid]

    # Build miners table
    miners = await build_miners_table(self.database, self.metagraph)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Miners table contains {len(miners)} elements")

    # Log event
    log_event(self, event, miners)
