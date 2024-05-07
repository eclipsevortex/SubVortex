from redis import asyncio as aioredis

current = "2.0.0"


async def rollout(database: aioredis.Redis):
    async for key in database.scan_iter("stats:*"):
        metadata_dict = await database.hgetall(key)

        if b"subtensor_successes" not in metadata_dict:
            await database.hset(key, b"subtensor_successes", 0)
        if b"subtensor_attempts" not in metadata_dict:
            await database.hset(key, b"subtensor_attempts", 0)
        if b"metric_successes" not in metadata_dict:
            await database.hset(key, b"metric_successes", 0)
        if b"metric_attempts" not in metadata_dict:
            await database.hset(key, b"metric_attempts", 0)
        if b"total_successes" not in metadata_dict:
            await database.hset(key, b"total_successes", 0)
        if b"tier" not in metadata_dict:
            await database.hset(key, b"tier", "Bronze")

    await database.set("version", current)


async def rollback(database: aioredis.Redis):
    async for key in database.scan_iter("stats:*"):
        metadata_dict = await database.hgetall(key)

        if b"subtensor_successes" in metadata_dict:
            await database.hdel(key, b"subtensor_successes")
        if b"subtensor_attempts" in metadata_dict:
            await database.hdel(key, b"subtensor_attempts")
        if b"metric_successes" in metadata_dict:
            await database.hdel(key, b"metric_successes")
        if b"metric_attempts" in metadata_dict:
            await database.hdel(key, b"metric_attempts")
        if b"total_successes" in metadata_dict:
            await database.hdel(key, b"total_successes")
        if b"tier" in metadata_dict:
            await database.hdel(key, b"tier")

    await database.set("version", None)
