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
    RELIABILLITY_FAILURE_REWARD,
    AVAILABILITY_WEIGHT,
    LATENCY_WEIGHT,
    RELIABILLITY_WEIGHT,
    DISTRIBUTION_WEIGHT,
)
from subnet.shared.subtensor import get_current_block
from subnet.validator.event import EventSchema
from subnet.validator.utils import (
    get_next_uids,
    ping_uid,
    get_available_uids,
    build_miners_table,
)
from subnet.validator.localisation import get_country
from subnet.validator.bonding import update_statistics
from subnet.validator.state import log_event
from subnet.validator.score import (
    compute_availability_score,
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
        return uid, available, country, DEFAULT_PROCESS_TIME

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

        # Check both blocks are the same
        verified = miner_block == validator_block or miner_block is not None

        bt.logging.trace(
            f"[{CHALLENGE_NAME}][{uid}] Verified ? {verified} - val: {validator_block}, miner:{miner_block}"
        )
    except Exception:
        verified = False
        process_time = DEFAULT_PROCESS_TIME if process_time is None else process_time
        bt.logging.warning(f"[{CHALLENGE_NAME}][{uid}] Subtensor not verified")

    return uid, verified, country, process_time


async def challenge_data(self):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Select the miners
    validator_hotkey = self.metagraph.hotkeys[self.uid]
    uids = await get_next_uids(self, validator_hotkey, k=10)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Get the countries
    miners_countries = {}
    for idx, (uid) in enumerate(get_available_uids(self)):
        ip = self.metagraph.axons[uid].ip
        miners_countries[f"{uid}"] = get_country(ip)
    bt.logging.debug(
        f"[{CHALLENGE_NAME}] Country loaded for {len(miners_countries)} uids"
    )

    # Initialise the miners table
    miners = await build_miners_table(self, miners_countries)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Miners table contains {len(miners)} elements")

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

    bt.logging.info(f"[{CHALLENGE_NAME}] Computing uids scores")

    # Compute the score
    for idx, (uid, verified, _, process_time) in enumerate(responses):
        # Compute the scores if only one miner is running on the axon machine
        miner = [miner for miner in miners if int(miner["uid"]) == uid][0]

        # Store verified
        miner["verified"] = verified

        # Check # of miners per IP - Only one miner per IP is allowed
        ip = self.metagraph.axons[uid].ip
        miners_on_ip = [
            self.metagraph.axons[uid].ip
            for uid in self.metagraph.uids.tolist()
            if self.metagraph.axons[uid].ip == ip
        ]
        number_of_miners = len(miners_on_ip)

        # Miner is verified if miner/subtensor are up and running and no more than 1 miner
        miner["verified"] = verified and number_of_miners == 1

        if number_of_miners == 1:
            # Set other statistics for verified miners only
            miner["process_time"] = process_time

            # Compute score for availability
            miner["availability_score"] = compute_availability_score(verified)
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{uid}] Availability score {miner['availability_score']}"
            )

            # Compute score for latency
            miner["latency_score"] = compute_latency_score(
                verified, uid, self.country, responses, miners
            )
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{uid}] Latency score {miner['latency_score']}"
            )

            # Compute score for reliability
            miner["reliability_score"] = await compute_reliability_score(
                verified, uid, miner
            )
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{uid}] Reliability score {miner['reliability_score']}"
            )

            # Compute score for distribution
            miner["distribution_score"] = compute_distribution_score(
                verified, uid, miners_countries
            )
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{uid}] Distribution score {miner['distribution_score']}"
            )

            # Compute final score
            miner["score"] = rewards[idx] = (
                (AVAILABILITY_WEIGHT * miner["availability_score"])
                + (LATENCY_WEIGHT * miner["latency_score"])
                + (RELIABILLITY_WEIGHT * miner["reliability_score"])
                + (DISTRIBUTION_WEIGHT * miner["distribution_score"])
            ) / (
                AVAILABILITY_WEIGHT
                + LATENCY_WEIGHT
                + RELIABILLITY_WEIGHT
                + DISTRIBUTION_WEIGHT
            )
        else:
            # More than 1 miner running in the axon machine
            # Someone is trying to hack => Penalize all the miners on the axon machine
            miner["process_time"] = 0
            miner["availability_score"] = 0
            miner["latency_score"] = 0
            miner["reliability_score"] = 0
            miner["distribution_score"] = 0
            miner["score"] = rewards[idx] = 0
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
                availability=miner["availability_score"],
                latency=miner["latency_score"],
                reliability=miner["reliability_score"],
                distribution=miner["distribution_score"],
                score=rewards[idx],
            ),
            deserialize=True,
            timeout=5,
        )

        # Set the miner version
        miner["version"] = (
            response[0] if len(response[0]) > 0 and response[0] != "" else "0.0.0"
        )

    # Update statistics in database
    await update_statistics(self, miners)

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
    # event.moving_averaged_scores = self.moving_averaged_scores.tolist()
    bt.logging.trace(
        f"[{CHALLENGE_NAME}] Updated moving avg scores: {self.moving_averaged_scores}"
    )

    # Display step time in seconds
    forward_time = time.time() - start_time
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")

    # Log event
    log_event(self, uids, miners, forward_time, self.moving_averaged_scores.tolist())
