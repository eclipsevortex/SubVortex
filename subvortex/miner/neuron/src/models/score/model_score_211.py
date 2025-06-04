from redis import asyncio as Redis

from subvortex.miner.neuron.src.models.score import Score


class ScoreModel:
    """
    Versioned model for storing and retrieving hotkey score from Redis.
    This is version 2.1.1 of the model.
    """

    version = "2.1.1"

    def _key(self, ss58_address: str) -> str:
        return f"sv:score:{ss58_address}"

    async def write(self, redis: Redis, score: Score):
        """
        Write score for a given hotkey.

        Converts all values to string before storing.
        """
        key = self._key(score.block)
        data = Score.to_dict(score)
        await redis.hset(key, mapping=data)
