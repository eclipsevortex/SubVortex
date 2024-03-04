import time
import typing
import asyncio
import torch
import bittensor as bt

from subnet import protocol
from subnet.constants import SUBTENSOR_FAILURE_REWARD
from subnet.validator.utils import get_available_query_miners
from subnet.validator.bonding import get_tier_factor, update_statistics
from subnet.validator.reward import apply_reward_scores


CHALLENGE_NAME = "Subtensor"
CHALLENGE_TIMEOUT = 5


async def handle_synapse(self, uid: int) -> typing.Tuple[bool, protocol.Subtensor]:
    response = await self.dendrite(
        axons=[self.metagraph.axons[uid]],
        synapse=protocol.Subtensor(task=1),
        deserialize=True,
        timeout=CHALLENGE_TIMEOUT,
    )

    try:
        # Create a subtensor with the ip return by the synapse
        config = bt.subtensor.config()
        config.subtensor.network = "local"
        config.subtensor.chain_endpoint = f"ws://{response[0].subtensor_ip}:9944"
        miner_subtensor = bt.subtensor(config)

        # Get the current block
        current_block = miner_subtensor.get_current_block()
        verified = current_block is not None
    except Exception:
        verified = False

    return verified, response


async def subtensor_data(self):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Send synapse to miners to get their ip
    tasks = []
    responses = []
    for uid in uids:
        tasks.append(asyncio.create_task(handle_synapse(self, uid)))
    responses = await asyncio.gather(*tasks)

    rewards: torch.FloatTensor = torch.zeros(len(responses), dtype=torch.float32).to(
        self.device
    )
    process_times: torch.FloatTensor = torch.zeros(len(responses), dtype=torch.float32).to(
        self.device
    )

    for idx, (uid, (verified, response)) in enumerate(zip(uids, responses)):
        if not verified:
            message = f"[{CHALLENGE_NAME}][{uid}] The subtensor is verified"
            bt.logging.success(message)
        else:
            message = f"[{CHALLENGE_NAME}][{uid}] The subtensor could not be verified"
            bt.logging.warning(message)

        # Get the coldkey
        axon = self.metagraph.axons[idx]
        coldkey = axon.coldkey

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Update subtensor
        subs_key = f"subs:{coldkey}:{hotkey}"
        await self.database.hset(subs_key, "ip", response[0].subtensor_ip)

        # # Update statistics
        # stats_key = f"stats:{hotkey}"
        # await self.database.hset(stats_key, "available", verified)
        # await self.database.hset(stats_key, "latency", response[0].dendrite.process_time)

        # Update statistics
        await update_statistics(
            ss58_address=hotkey,
            success=verified,
            task_type="subtensor",
            database=self.database,
        )

        # Apply reward the challenge
        rewards[idx] = 1.0 if verified else SUBTENSOR_FAILURE_REWARD

        # Get the process time for each uid to apply the rewards accordingly
        process_time = float(response.process_time) if verified else CHALLENGE_TIMEOUT
        process_times.append(process_time)
        bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Process time {process_time}")

    # Apply rewards to the miners
    bt.logging.trace(f"[{CHALLENGE_NAME}] Applying rewards")
    apply_reward_scores(
        self,
        uids=uids,
        rewards=rewards,
        process_times=process_times,
        timeout=CHALLENGE_TIMEOUT,
    )

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")
