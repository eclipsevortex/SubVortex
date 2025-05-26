from redis import asyncio as aioredis

revision = "2.1.0"
down_revision = "2.0.0"


async def _rename_keys(database: aioredis.Redis, old_prefix: str, new_prefix: str):
    async for old_key in database.scan_iter(f"{old_prefix}:*"):
        old_key_str = old_key.decode()
        suffix = old_key_str[len(old_prefix) + 1 :]
        new_key = f"{new_prefix}:{suffix}"
        await database.rename(old_key_str, new_key)


async def rollout(database: aioredis.Redis):
    # Validator rollout
    await _rename_keys(database, "stats", "sv:miner")
    await _rename_keys(database, "selection", "sv:selection")


async def rollback(database: aioredis.Redis):
    # Validator rollback
    await _rename_keys(database, "sv:miner", "stats")
    await _rename_keys(database, "sv:selection", "selection")

    # Neuron rollback
    keys_to_delete = [
        "sv:state:metagraph:stream",
        "sv:state:neuron:last_updated",
        "sv:state:metagraph",
    ]
    async for key in database.scan_iter("sv:neuron:*"):
        keys_to_delete.append(key)

    if keys_to_delete:
        await database.delete(*keys_to_delete)
