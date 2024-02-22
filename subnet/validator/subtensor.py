import time
import typing
import asyncio
import bittensor as bt

from subnet import protocol
from subnet.validator.utils import get_available_query_miners


async def handle_synapse(self, uid: int) -> typing.Tuple[bool, protocol.Subtensor]:
    response = await self.dendrite(
        axons=[self.metagraph.axons[uid]],
        synapse=protocol.Subtensor(task=1),
        deserialize=True,
    )

    # Check the subtensor ip returned by the miner is an up and running subtensor
    # TODO: restore once we have reinstall the local subtensor correctly in our VPS test
    # try:
    #     # Create a subtensor with the ip return by the synapse
    #     config = bt.subtensor.config()
    #     config.subtensor.network = "local"
    #     config.subtensor.chain_endpoint = f"ws://{response[0].subtensor_ip}:9944"
    #     miner_subtensor = bt.subtensor(config)

    #     # Get the current block
    #     current_block = miner_subtensor.get_current_block()
    #     verified = current_block is not None
    # except Exception:
    #     verified = False

    verified = True

    return verified, response


async def subtensor_data(self):
    start_time = time.time()

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"subtensor uids {uids}")

    # Send synapse to miners to get their ip
    tasks = []
    responses = []
    for uid in uids:
        tasks.append(asyncio.create_task(handle_synapse(self, uid)))
    responses = await asyncio.gather(*tasks)

    for idx, (uid, (verified, response)) in enumerate(zip(uids, responses)):
        if not verified:
            # TODO: do we punished miner now, later or never?
            continue

        subtensor_ip = response[0].subtensor_ip

        # Get the coldkey
        axon = self.metagraph.axons[idx]
        coldkey = axon.coldkey

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Get the subs hash
        subs_key = f"subs:{coldkey}:{hotkey}"

        await self.database.hset(subs_key, "ip", subtensor_ip)

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.info(f"subtensor step time: {forward_time:.2f}s")