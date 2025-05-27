from redis import asyncio as Redis

from subvortex.validator.core.model.challenge import Challenge
from subvortex.core.database.database_utils import decode_hash


class ChallengeModel:
    """
    Versioned model for storing and retrieving hotkey challenge from Redis.
    This is version 2.1.0 of the model.
    """

    version = "2.1.0"

    def _key(self, hotkey: str) -> str:
        return f"sv:challenge:{hotkey}"

    async def read(self, redis: Redis, hotkey: str) -> Challenge | None:
        key = self._key(hotkey)
        raw = await redis.hgetall(key)
        if not raw:
            return None
        data = decode_hash(raw)
        return Challenge.from_dict(data)

    async def read_all(self, redis: Redis) -> dict[str, Challenge]:
        miners: dict[str, Challenge] = {}

        async for key in redis.scan_iter(match=self._key("*")):
            decoded_key = key.decode()
            raw = await redis.hgetall(decoded_key)
            if not raw:
                continue

            ss58_address = decoded_key.split("sv:challenge:")[1]
            data = decode_hash(raw)
            miners[ss58_address] = Challenge.from_dict(data)

        return miners

    async def write(self, redis: Redis, hotkey: str, challenge: Challenge):
        key = self._key(hotkey)
        data = Challenge.to_dict(challenge)
        await redis.hmset(key, data)

    async def write_all(self, redis: Redis, schedules: list[Challenge]):
        async with redis.pipeline() as pipe:
            for challenge in schedules:
                key = self._key(challenge.hotkey)
                data = Challenge.to_dict(challenge)
                pipe.hmset(key, data)
            await pipe.execute()

    async def delete(self, redis: Redis, hotkey: str):
        key = self._key(hotkey)
        await redis.delete(key)

    async def delete_all(self, redis: Redis, schedules: list[Challenge]):
        async with redis.pipeline() as pipe:
            for challenge in schedules:
                key = self._key(challenge.hotkey)
                pipe.delete(key)
            await pipe.execute()
