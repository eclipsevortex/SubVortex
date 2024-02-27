import time
import typing
import asyncio
import bittensor as bt

from subnet import protocol
from subnet.validator.event import EventSchema
from subnet.validator.utils import get_available_query_miners


async def handle_synapse(self, uid: int) -> typing.Tuple[bool, protocol.Subtensor]:
    response = await self.dendrite(
        axons=[self.metagraph.axons[uid]],
        synapse=protocol.Subtensor(task=1),
        deserialize=True,
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


async def subtensor_data(self, event: EventSchema):
    start_time = time.time()
    bt.logging.debug(f"[Subtensor] Starting")

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"[Subtensor] Available uids {uids}")

    # Send synapse to miners to get their ip
    tasks = []
    responses = []
    for uid in uids:
        tasks.append(asyncio.create_task(handle_synapse(self, uid)))
    responses = await asyncio.gather(*tasks)

    for idx, (uid, (verified, response)) in enumerate(zip(uids, responses)):
        # Get the coldkey
        axon = self.metagraph.axons[idx]
        cold_key = axon.coldkey

        # Get the hotkey
        hot_key = self.metagraph.hotkeys[uid]

        # Get the subs hash
        subs_key = f"subs:{cold_key}:{hot_key}"

        if False and not verified:
            event.uid.append(uid)
            event.ip.append(None)
            event.cold_key.append(cold_key)
            event.hot_key.append(hot_key)
            continue

        subtensor_ip = response[0].subtensor_ip
        if not subtensor_ip:
            event.uid.append(uid)
            event.ip.append(None)
            event.cold_key.append(cold_key)
            event.hot_key.append(hot_key)
            continue

        # Update event
        event.uid.append(uid)
        event.ip.append(subtensor_ip)
        event.cold_key.append(cold_key)
        event.hot_key.append(hot_key)

        # # Send data to the subvortex api
        # await self.api.send({"type": "subtensor", "key": subs_key, "ip": subtensor_ip})
        # bt.logging.info(f"[Subtensor][{uid}] Data send to SubVortex api")

        await self.database.hset(subs_key, "ip", subtensor_ip)
        bt.logging.info(f"[Subtensor][{uid}] Data cached into redis")

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[Subtensor] Step time {forward_time:.2f}s")

    return event
