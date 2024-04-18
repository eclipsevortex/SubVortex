import torch
import time
import asyncio
import bittensor as bt

from subnet.constants import DEFAULT_PROCESS_TIME
from subnet.shared.substrate import (
    get_sync_state,
    get_node_peer_id,
    get_listen_addresses,
)
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


CHALLENGE_NAME = "Challenge"


async def handle_synapse(self, uid: int):
    # Get the miner
    miner: Miner = next((miner for miner in self.miners if miner.uid == uid), None)

    # Check the miner is available
    result = await ping_uid(self, miner.uid)
    if result != 1:
        miner.verified = False
        miner.owner = result == 0
        miner.process_time = DEFAULT_PROCESS_TIME
        return "Miner is not verified"

    bt.logging.trace(f"[{CHALLENGE_NAME}][{miner.uid}] Miner verified")

    verified = False
    reason = None
    primary = True
    process_time: float = DEFAULT_PROCESS_TIME
    try:
        # Start the timer
        start_time = time.time()

        # Get the peer id of the subtensor
        request_id = self.subtensor.substrate.request_id + 1
        peer_id = get_node_peer_id(miner.ip, request_id)
        bt.logging.trace(f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor peer id {peer_id}")

        # Get the listen addresses
        request_id = self.subtensor.substrate.request_id + 1
        addresses = get_listen_addresses(miner.ip, request_id)
        bt.logging.trace(
            f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor listen addresses {addresses}"
        )

        # Check the ownership of the subtensor
        address = f"/ip4/{miner.ip}/tcp/30333/ws/p2p/{peer_id}"
        owner = address in addresses
        if not primary:
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor is own by someone else"
            )

        # Check the state of the subtensor
        request_id = self.subtensor.substrate.request_id + 1
        state = get_sync_state(miner.ip, request_id)
        bt.logging.trace(f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor state {state}")
        is_sync = state.get("currentBlock") == state.get("highestBlock")
        if not is_sync:
            bt.logging.debug(
                f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor is desynchronised"
            )

        # Compute the process time
        process_time = time.time() - start_time

        # Check if subtensor is verified
        verified = owner and is_sync
        if verified:
            bt.logging.trace(f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor verified")
        else:
            reason = "Subtensor is not verified"
    except Exception as ex:
        verified = False
        bt.logging.warning(
            f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor not verified: {ex}"
        )
        reason = "Subtensor is not verified"

    # Update the miner object
    finally:
        miner.verified = verified
        miner.process_time = process_time
        miner.owner = owner

    return reason


async def challenge_data(self):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Select the miners
    val_hotkey = self.metagraph.hotkeys[self.uid]
    uids = await get_next_uids(self, val_hotkey)
    uids = uids[:-2] + [28, 66]
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

        if not miner.owner:
            primary_uid = next(
                (x.uid for x in self.miners if x.primary and x.ip == miner.ip), None
            )
            bt.logging.error(
                f"[{CHALLENGE_NAME}][{miner.uid}] Miner is using the subtenosr of the uid {primary_uid}"
            )

        if not miner.verified:
            bt.logging.warning(f"[{CHALLENGE_NAME}][{miner.uid}] {reasons[idx]}")

        # Check the miner's ip is not used by multiple miners (1 miner = 1 ip)
        if miner.ip_occurences != 1:
            bt.logging.warning(
                f"[{CHALLENGE_NAME}][{miner.uid}] {miner.ip_occurences} miner(s) associated with the ip"
            )

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
