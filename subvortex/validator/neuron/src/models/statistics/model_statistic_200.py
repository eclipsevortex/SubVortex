from typing import Optional, Dict, Any
from redis import asyncio as Redis

from subvortex.validator.core.database import get_field_value


class StatisticModel:
    """
    Versioned model for storing and retrieving hotkey statistics from Redis.
    This is version 2.0.0 of the model.
    """

    version = "2.0.0"

    def redis_key(self, ss58_address: str) -> str:
        """Generate the Redis key for a given hotkey."""
        return f"stats:{ss58_address}"

    async def read(self, redis: Redis, ss58_address: str) -> Optional[Dict[str, Any]]:
        """
        Read statistics for a given hotkey.

        Returns:
            Dictionary of decoded and typed values, or None if not found.
        """
        key = self.redis_key(ss58_address)
        raw_data = await redis.hgetall(key)

        if not raw_data:
            return None

        return {
            "country": get_field_value(raw_data.get(b"country")),
            "version": get_field_value(raw_data.get(b"version"), default="0.0.0"),
            "verified": get_field_value(raw_data.get(b"verified"), default="0") == "1",
            "score": get_field_value(
                raw_data.get(b"score"), default=0, cast_type=float
            ),
            "availability_score": get_field_value(
                raw_data.get(b"availability_score"), default=0, cast_type=float
            ),
            "latency_score": get_field_value(
                raw_data.get(b"latency_score"), default=0, cast_type=float
            ),
            "reliability_score": get_field_value(
                raw_data.get(b"reliability_score"), default=0, cast_type=float
            ),
            "distribution_score": get_field_value(
                raw_data.get(b"distribution_score"), default=0, cast_type=float
            ),
            "challenge_successes": get_field_value(
                raw_data.get(b"challenge_successes"), default=0, cast_type=int
            ),
            "challenge_attempts": get_field_value(
                raw_data.get(b"challenge_attempts"), default=0, cast_type=int
            ),
            "process_time": get_field_value(
                raw_data.get(b"process_time"), default=0, cast_type=float
            ),
        }

    async def write(self, redis: Redis, ss58_address: str, data: Dict[str, Any]):
        """
        Write statistics for a given hotkey.

        Converts all values to string before storing.
        """
        key = self.redis_key(ss58_address)

        encoded_data = {
            "country": data.get("country", ""),
            "version": data.get("version", self.version),
            "verified": str(data.get("verified", "0")),
            "score": str(data.get("score", 0)),
            "availability_score": str(data.get("availability_score", 0)),
            "latency_score": str(data.get("latency_score", 0)),
            "reliability_score": str(data.get("reliability_score", 0)),
            "distribution_score": str(data.get("distribution_score", 0)),
            "challenge_successes": str(data.get("challenge_successes", 0)),
            "challenge_attempts": str(data.get("challenge_attempts", 0)),
            "process_time": str(data.get("process_time", 0)),
        }

        await redis.hset(key, mapping=encoded_data)

    async def delete(self, redis: Redis, ss58_address: str):
        """
        Delete the statistics entry for a given hotkey.
        """
        key = self.redis_key(ss58_address)
        await redis.delete(key)
