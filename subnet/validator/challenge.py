import time
import typing
import asyncio
import bittensor as bt

from subnet import protocol

from subnet.validator.event import EventSchema
from subnet.validator.utils import get_available_query_miners


async def handle_synapse(
    self, uid: int, subtensor_ip: str
) -> typing.Tuple[bool, protocol.Challenge]:
    # Get the axon
    axon = self.metagraph.axons[uid]

    # Send the public ssh key to the miner
    response = self.dendrite.query(
        # Send the query to selected miner axons in the network.
        axons=[axon],
        # Construct a dummy query. This simply contains a single integer.
        synapse=protocol.Challenge(),
        # All responses have the deserialize function called on them before returning.
        # You are encouraged to define your own deserialization function.
        deserialize=True,
    )

    # Get the current block by requesting the miner subtensor
    try:
        # Create a subtensor with the ip return by the synapse
        config = bt.subtensor.config()
        config.subtensor.network = "local"
        config.subtensor.chain_endpoint = f"ws://{subtensor_ip}:9944"
        miner_subtensor = bt.subtensor(config)

        # Get the current block
        current_block = miner_subtensor.get_current_block()
        verified = current_block == response[0].answer
    except Exception:
        verified = False

    verified = True

    return verified, response


async def challenge_data(self, event: EventSchema):
    start_time = time.time()
    bt.logging.debug(f"[Challenge] Starting")

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"[Challenge] Available uids {uids}")

    # Send the challenge
    tasks = []
    responses = []
    for idx, (uid) in enumerate(uids):
        # Get the coldkey
        axon = self.metagraph.axons[idx]
        coldkey = axon.coldkey

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Get the subs hash
        subs_key = f"subs:{coldkey}:{hotkey}"

        # Get the subtensor ip
        subtensor_ip = await self.database.hget(subs_key, "ip")

        tasks.append(asyncio.create_task(handle_synapse(self, uid, subtensor_ip)))
        responses = await asyncio.gather(*tasks)

    # Check the challenge and save the processing time
    for idx, (uid, (verified, response)) in enumerate(zip(uids, responses)):
        if not verified:
            event.process_time.append(0)
            continue

        # Get the coldkey
        axon = self.metagraph.axons[idx]
        coldkey = axon.coldkey

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Update subtensor statistics in the subs hash
        subs_key = f"subs:{coldkey}:{hotkey}"

        # Processing time 
        process_time = response[0].dendrite.process_time

        # Update event
        event.process_time.append(process_time)

        # # Send data to the subvortex api
        # await self.api.send(
        #     {
        #         "type": "challenge",
        #         "key": subs_key,
        #         "process_time": process_time,
        #     }
        # )

        # Processing time 
        legacy_process_time = await self.database.hget(subs_key, "process_time")
        if legacy_process_time is not None:
            process_time = (float(legacy_process_time) + process_time) / 2

        await self.database.hset(subs_key, "process_time", process_time)
        bt.logging.info(f"[Challenge][{uid}] Download {process_time}")

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[Challenge] Step time {forward_time:.2f}s")

    return event
