from redis import asyncio as aioredis

revision = "3.0.0"
down_revision = "2.0.0"


async def rollout(database: aioredis.Redis):
    await database.set(b"newkey", 1)

async def rollback(database: aioredis.Redis):
    await database.delete(b"newkey", 1)
