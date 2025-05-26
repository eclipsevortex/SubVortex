from redis import asyncio as aioredis

revision = "1.0.0"
down_revision = None


async def rollout(database: aioredis.Redis):
    pass


async def rollback(database: aioredis.Redis):
    # Neuron rollback
    keys_to_delete = [
        "sv:state:metagraph:stream",
        "sv:state:neuron:last_updated",
        "sv:state:metagraph",
    ]
    async for key in database.scan_iter("sv:neuron:*"):
        keys_to_delete.append(key)
