from typing import Optional, Dict, Any
from redis import asyncio as Redis

from subvortex.validator.core.database import get_field_value


class SelectionModel:
    """
    Versioned model for storing and retrieving hotkey statistics from Redis.
    This is version 2.0.0 of the model.
    """

    version = "2.0.0"

    def redis_key(self, ss58_address: str) -> str:
        return f"selection:{ss58_address}"

    async def read(self, redis: Redis, ss58_address: str) -> Optional[Dict[str, Any]]:
        value = await redis.get(self.redis_key(ss58_address))
        if value is None:
            return []

        uids_str = get_field_value(value)
        return [int(uid) for uid in uids_str.split(",") if uid.strip().isdigit()]

    async def write(self, redis: Redis, ss58_address: str, selection: list[int]):
        """
        Store the list of selected miner UIDs in Redis as a comma-separated string.
        """
        selection_str = ",".join(str(uid) for uid in selection)
        await redis.set(self.redis_key(ss58_address), selection_str)
