from redis import asyncio as Redis

from subvortex.validator.core.model.schedule import Schedule
from subvortex.core.database.database_utils import decode_hash


class ScheduleModel:
    """
    Versioned model for storing and retrieving hotkey schedule from Redis.
    This is version 2.1.0 of the model.
    """

    version = "2.1.0"

    def _key(self, hotkey: str) -> str:
        return f"sv:schedule:{hotkey}"

    async def read(self, redis: Redis, hotkey: str) -> Schedule | None:
        key = self._key(hotkey)
        raw = await redis.hgetall(key)
        if not raw:
            return None
        data = decode_hash(raw)
        return Schedule.from_dict(data)

    async def read_all(self, redis: Redis) -> dict[str, Schedule]:
        miners: dict[str, Schedule] = {}

        async for key in redis.scan_iter(match=self._key("*")):
            decoded_key = key.decode()
            raw = await redis.hgetall(decoded_key)
            if not raw:
                continue

            ss58_address = decoded_key.split("sv:schedule:")[1]
            data = decode_hash(raw)
            miners[ss58_address] = Schedule.from_dict(data)

        return miners

    async def write(self, redis: Redis, hotkey: str, schedule: Schedule):
        key = self._key(hotkey)
        data = Schedule.to_dict(schedule)
        await redis.hmset(key, data)

    async def write_all(self, redis: Redis, schedules: list[Schedule]):
        async with redis.pipeline() as pipe:
            for schedule in schedules:
                key = self._key(schedule.hotkey)
                data = Schedule.to_dict(schedule)
                pipe.hmset(key, data)
            await pipe.execute()

    async def delete(self, redis: Redis, hotkey: str):
        key = self._key(hotkey)
        await redis.delete(key)

    async def delete_all(self, redis: Redis, schedules: list[Schedule]):
        async with redis.pipeline() as pipe:
            for schedule in schedules:
                key = self._key(schedule.hotkey)
                pipe.delete(key)
            await pipe.execute()
