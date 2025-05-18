from redis import asyncio as Redis

from subvortex.core.database.database_utils import decode_hash
from subvortex.validator.neuron.src.models.statistics import Statistic


class StatisticModel:
    """
    Versioned model for storing and retrieving hotkey statistics from Redis.
    This is version 2.0.0 of the model.
    """

    version = "2.0.0"

    def redis_key(self, ss58_address: str) -> str:
        """Generate the Redis key for a given hotkey."""
        return f"stats:{ss58_address}"

    async def read(self, redis: Redis, ss58_address: str) -> Statistic | None:
        """
        Read statistics for a given hotkey.

        Returns:
            Dictionary of decoded and typed values, or None if not found.
        """
        key = self.redis_key(ss58_address)
        raw = await redis.hgetall(key)
        data = decode_hash(raw)
        return Statistic.from_redis_mapping(data)

    async def write(self, redis: Redis, ss58_address: str, statistic: Statistic):
        """
        Write statistics for a given hotkey.

        Converts all values to string before storing.
        """
        key = self.redis_key(ss58_address)
        data = Statistic.to_redis_mapping(statistic)
        await redis.hset(key, mapping=data)

    async def delete(self, redis: Redis, ss58_address: str):
        """
        Delete the statistics entry for a given hotkey.
        """
        key = self.redis_key(ss58_address)
        await redis.delete(key)
