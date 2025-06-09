from redis import asyncio as Redis

from subvortex.core.database.database_utils import decode_hash
from subvortex.validator.neuron.src.models.miner import Miner


class MinerModel:
    """
    Versioned model for storing and retrieving hotkey miner from Redis.
    This is version 2.1.0 of the model.
    """

    version = "2.1.0"

    def _key(self, ss58_address: str) -> str:
        return f"sv:miner:{ss58_address}"

    async def read(self, redis: Redis, ss58_address: str) -> Miner | None:
        """
        Read statistics for a given hotkey.

        Returns:
            Dictionary of decoded and typed values, or None if not found.
        """
        key = self._key(ss58_address)
        raw = await redis.hgetall(key)
        if not raw:
            return None

        data = decode_hash(raw)
        return Miner.from_dict(data, ss58_address)

    async def read_all(self, redis: Redis) -> dict[str, Miner]:
        """
        Read all Miner entries stored under 'sv:miner:*'.

        Returns:
            Dictionary mapping ss58_address to Miner object.
        """
        miners: dict[str, Miner] = {}

        async for key in redis.scan_iter(match=self._key("*")):
            ss58_address = key.decode().split("sv:miner:")[1]
            raw = await redis.hgetall(key)
            if not raw:
                continue

            data = decode_hash(raw)
            miners[ss58_address] = Miner.from_dict(data, ss58_address)

        return miners

    async def write(self, redis: Redis, miner: Miner):
        """
        Write statistics for a given hotkey.

        Converts all values to string before storing.
        """
        key = self._key(miner.hotkey)
        data = Miner.to_dict(miner)
        await redis.hset(key, mapping=data)

    async def write_all(self, redis: Redis, miners: list[Miner]):
        """
        Writes multiple Miner entries in bulk using a pipeline.
        """
        pipe = redis.pipeline()

        for miner in miners:
            key = self._key(miner.hotkey)
            data = Miner.to_dict(miner)
            pipe.hset(key, mapping=data)

        await pipe.execute()

    async def delete(self, redis: Redis, miner: Miner):
        """
        Delete the statistics entry for a given hotkey.
        """
        key = self._key(miner.hotkey)
        await redis.delete(key)

    async def delete_all(self, redis: Redis, miners: list[Miner]):
        """
        Delete the statistics entry for a given hotkey.
        """
        pipe = redis.pipeline()

        for miner in miners:
            key = self._key(miner.hotkey)
            pipe.delete(key)

        await pipe.execute()
