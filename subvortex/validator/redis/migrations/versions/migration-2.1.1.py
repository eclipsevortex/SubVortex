from redis import asyncio as aioredis

revision = "2.1.1"
down_revision = "2.1.0"


def decode_hash(raw: dict[bytes, bytes]) -> dict[str, str]:
    return {k.decode(): v.decode() for k, v in raw.items()}


async def rollout(database: aioredis.Redis):
    async for key in database.scan_iter(match="sv:miner:*"):
        # Get the miner hotkey
        hotkey = key.decode().split("sv:miner:")[1]

        # Fetch neuron
        raw_neuron = await database.hgetall(f"sv:neuron:{hotkey}")
        if not raw_neuron:
            # Skip if neuron not found
            continue

        # Decode the neuron
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
        await database.hdel(key, "ip", "hotkey")
