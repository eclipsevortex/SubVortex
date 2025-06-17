from redis import asyncio as Redis

from subvortex.core.database.database_utils import decode_hash
from subvortex.validator.core.model.score import Score


class ScoreModel:
    """
    Versioned model for storing and retrieving scores from Redis.
    This is version 2.1.0 of the model.
    """

    version = "2.1.0"

    def _key(self, hotkey: str = "*", node_id: str = "*") -> str:
        return f"sv:score:{hotkey}:{node_id}"

    async def read(self, redis: Redis, node_id: str) -> Score | None:
        key = self._key(node_id)
        raw = await redis.hgetall(key)
        if not raw:
            return None

        data = decode_hash(raw)
        return Score.from_dict(data, node_id)

    async def read_by_hotkey(self, redis: Redis, hotkey: str) -> dict[str, Score]:
        scores: dict[str, Score] = {}

        async for key in redis.scan_iter(match=self._key(hotkey)):
            node_id = key.decode().split(f"sv:score:{hotkey}")[1]
            raw = await redis.hgetall(key)
            if not raw:
                continue

            data = decode_hash(raw)
            scores[node_id] = Score.from_dict(data)

        return scores

    async def write(self, redis: Redis, score: Score):
        key = self._key(score.hotkey, score.node_id)
        data = Score.to_dict(score)
        await redis.hset(key, mapping=data)

    async def write_all(self, redis: Redis, scores: list[Score]):
        pipe = redis.pipeline()

        for score in scores:
            key = self._key(score.hotkey, score.node_id)
            data = Score.to_dict(score)
            pipe.hset(key, mapping=data)

        await pipe.execute()

    async def delete(self, redis: Redis, score: Score):
        """
        Delete the statistics entry for a given hotkey.
        """
        key = self._key(score.hotkey, score.node_id)
        await redis.delete(key)

    async def delete_all(self, redis: Redis, scores: list[Score]):
        """
        Delete the statistics entry for a given hotkey.
        """
        pipe = redis.pipeline()

        for score in scores:
            key = self._key(score.hotkey, score.node_id)
            pipe.delete(key)

        await pipe.execute()
