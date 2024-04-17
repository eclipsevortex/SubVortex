import torch
import time
import asyncio
import bittensor as bt

from subnet.constants import DEFAULT_PROCESS_TIME
from subnet.shared.subtensor import get_current_block
from subnet.validator.models import Miner
from subnet.validator.synapse import send_scope
from subnet.validator.utils import (
    get_next_uids,
    ping_uid,
)
from subnet.validator.bonding import update_statistics
from subnet.validator.state import log_event
from subnet.validator.score import (
    compute_availability_score,
    compute_reliability_score,
    compute_latency_score,
    compute_distribution_score,
    compute_final_score,
)
from substrateinterface.base import SubstrateInterface


CHALLENGE_NAME = "Challenge"


async def handle_synapse(self, uid: int):
    # Get the miner
    miner: Miner = next((miner for miner in self.miners if miner.uid == uid), None)
    miner.primary = True

    # Check the miner is available
    available = await ping_uid(self, miner.uid)
    if available != 1:
        miner.verified = False
        miner.primary = available != 2
        miner.process_time = DEFAULT_PROCESS_TIME
        return f"Miner is not reachable"

    bt.logging.trace(f"[{CHALLENGE_NAME}][{miner.uid}] Miner verified")

    verified = False
    reason = None
    process_time: float = DEFAULT_PROCESS_TIME
    try:
        # Create a subtensor with the ip return by the synapse
        substrate = SubstrateInterface(
            ss58_format=bt.__ss58_format__,
            use_remote_preset=True,
            url=f"ws://{miner.ip}:9944",
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
        verified = (
            miner_block == validator_block or (validator_block - miner_block) <= 1
        )
        if not verified:
            reason = "Subtensor is desynchronised"

        bt.logging.trace(
            f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor verified ? {verified} - val: {validator_block}, miner:{miner_block}"
        )
    except Exception as ex:
        verified = False
        reason = "Subtensor is not reachable"

    # Update the miner object
    finally:
        miner.verified = verified
        miner.process_time = process_time
    
    return reason


async def challenge_data(self):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Select the miners
    val_hotkey = self.metagraph.hotkeys[self.uid]
    uids = await get_next_uids(self, val_hotkey)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Execute the challenges
    tasks = []
    reasons = []
    for uid in uids:
        tasks.append(asyncio.create_task(handle_synapse(self, uid)))
        reasons = await asyncio.gather(*tasks)

    # Initialise the rewards object
    rewards: torch.FloatTensor = torch.zeros(len(uids), dtype=torch.float32).to(
        self.device
    )

    bt.logging.info(f"[{CHALLENGE_NAME}] Starting evaluation")

    # Compute the score
    for idx, (uid) in enumerate(uids):
        # Get the miner
        miner: Miner = next((miner for miner in self.miners if miner.uid == uid), None)

        bt.logging.info(f"[{CHALLENGE_NAME}][{miner.uid}] Computing score...")

        if not miner.primary:
            primary_uid = next((x.uid for x in self.miners if x.primary and x.ip == miner.ip), None)
            bt.logging.warning(f"[{CHALLENGE_NAME}][{miner.uid}] Miner flagged as secondary (Primary: {primary_uid})")

        if not miner.verified:
            bt.logging.warning(f"[{CHALLENGE_NAME}][{miner.uid}] {reasons[idx]}")

        # Compute score for availability
        miner.availability_score = compute_availability_score(miner)
        bt.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Availability score {miner.availability_score}"
        )

        # Compute score for latency
        miner.latency_score = compute_latency_score(self.country, miner, self.miners)
        bt.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Latency score {miner.latency_score}"
        )

        # Compute score for reliability
        miner.reliability_score = await compute_reliability_score(miner)
        bt.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Reliability score {miner.reliability_score}"
        )

        # Compute score for distribution
        miner.distribution_score = compute_distribution_score(miner, self.miners)
        bt.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Distribution score {miner.distribution_score}"
        )

        # Compute final score
        miner.score = compute_final_score(miner)
        rewards[idx] = miner.score
        bt.logging.info(f"[{CHALLENGE_NAME}][{miner.uid}] Final score {miner.score}")

        # Send the score details to the miner
        miner.version = await send_scope(self, miner, reasons[idx])

        # Save miner snapshot in database
        await update_statistics(self, miner)

    bt.logging.trace(f"[{CHALLENGE_NAME}] Rewards: {rewards}")

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
    # alpha of 0.05 means that each new score replaces 5% of the weight of the previous weights
    alpha: float = 0.05
    self.moving_averaged_scores = alpha * scattered_rewards + (
        1 - alpha
    ) * self.moving_averaged_scores.to(self.device)
    bt.logging.trace(
        f"[{CHALLENGE_NAME}] Updated moving avg scores: {self.moving_averaged_scores}"
    )

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")

    # Log event
    log_event(self, uids, forward_time)
