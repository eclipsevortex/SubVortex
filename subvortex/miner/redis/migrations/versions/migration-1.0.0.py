from redis import asyncio as aioredis

revision = "1.0.0"
down_revision = None

async def rollout(database: aioredis.Redis):
    pass

async def rollback(database: aioredis.Redis):
    # Remove all keys with prefix sv:neuron:
    keys_to_delete = []
    async for key in database.scan_iter("sv:neuron:*"):
        keys_to_delete.append(key)
    
    if keys_to_delete:
        await database.delete(*keys_to_delete)
