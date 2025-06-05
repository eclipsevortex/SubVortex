from redis import asyncio as Redis

from subvortex.miner.neuron.src.models.score import Score
from subvortex.core.database.database_utils import decode_hash


class ScoreModel:
    """
    Versioned model for storing and retrieving hotkey score from Redis.
    This is version 1.0.0 of the model.
    """

    version = "1.0.0"

    def _key(self, ss58_address: str) -> str:
        return f"sv:score:{ss58_address}"

    async def read_all(self, redis: Redis) -> dict[str, Score]:
        scores: dict[str, Score] = {}

        async for key in redis.scan_iter(match=self._key("*")):
            decoded_key = key.decode()
            raw = await redis.hgetall(decoded_key)
            if not raw:
                continue

            block = decoded_key.split(":")[-1]
            data = decode_hash(raw)
            scores[block] = Score.from_dict(data)

        return scores

    async def write(self, redis: Redis, score: Score):
        """
        Write score for a given hotkey.

        Converts all values to string before storing.
        """
        key = self._key(score.block)
        data = Score.to_dict(score)
        await redis.hset(key, mapping=data)

    async def prune(self, redis, max_entries: int):
        # Get all the keys
        pattern = self._key("*")
        keys = await redis.keys(pattern)

        # Extract block numbers and sort descending
        sorted_keys = sorted(
            keys, key=lambda k: int(k.decode().split(":")[-1]), reverse=True
        )

        # Keep only the most recent `max_entries`
        to_delete = sorted_keys[max_entries:]
        if not to_delete:
            return

        # Delete the oldest scores
        await redis.delete(*to_delete)
