from typing import Optional, Dict, Any, List
from redis import asyncio as Redis

from subvortex.core.database.database_utils import decode_value


class SelectionModel:
    """
    Versioned model for storing and retrieving hotkey statistics from Redis.
    This is version 2.0.0 of the model.
    """

    version = "2.0.0"

    def redis_key(self, ss58_address: str) -> List[int]:
        return f"selection:{ss58_address}"

    async def read(self, redis: Redis, ss58_address: str) -> Optional[Dict[str, Any]]:
        key = self.redis_key(ss58_address)
        raw = await redis.get(key)
        data = decode_value(raw) if raw else ""
        return [int(uid) for uid in data.split(",") if uid.strip().isdigit()]

    async def write(self, redis: Redis, ss58_address: str, uids: List[int]):
        """
        Store the list of selected miner UIDs in Redis as a comma-separated string.
        """
        key = self.redis_key(ss58_address)
        data = ",".join(str(uid) for uid in uids)
        await redis.set(key, data)
