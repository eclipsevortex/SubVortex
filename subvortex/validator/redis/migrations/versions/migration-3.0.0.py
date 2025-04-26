from redis import asyncio as aioredis


revision = "3.0.0"
down_revision = "2.0.0"


async def rollout(database: aioredis.Redis):
    await database.set("newkey", 0)


async def rollback(database: aioredis.Redis):
    await database.delete("newkey")
