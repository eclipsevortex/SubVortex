from redis import asyncio as aioredis

from subvortex.core.database.database_utils import decode_hash
from subvortex.validator.neuron.src.models.miner import Miner

revision = "2.1.1"
down_revision = "2.1.0"


async def rollout(database: aioredis.Redis):
    async for key in database.scan_iter(match="sv:miner:*"):
        # Get the miner hotkey
        hotkey = key.decode().split("sv:miner:")[1]

        # Fetch neuron
        raw_neuron = await database.hgetall(f"sv:neuron:{hotkey}")
        if not raw_neuron:
            # Skip if neuron not found
            continue

        neuron_data = decode_hash(raw_neuron)

        # Fetch miner
        raw_miner = await database.hgetall(key)
        miner_data = decode_hash(raw_miner)

        # Set IP from neuron
        miner_data["hotkey"] = hotkey
        miner_data["ip"] = neuron_data.get("ip", "0.0.0.0")

        await database.hset(key, mapping=miner_data)


async def rollback(database: aioredis.Redis):
    async for key in database.scan_iter(match="sv:miner:*"):
        await database.hdel(key, "ip")
