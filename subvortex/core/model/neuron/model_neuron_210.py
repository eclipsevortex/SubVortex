from redis import asyncio as Redis

from subvortex.core.model.neuron import Neuron
from subvortex.core.database.database_utils import decode_hash


class NeuronModel:
    """
    Versioned model for storing and retrieving hotkey neuron from Redis.
    This is version 2.1.0 of the model.
    """

    version = "2.1.0"

    def _key(self, hotkey: str) -> str:
        return f"sv:neuron:{hotkey}"

    async def read(self, redis: Redis, hotkey: str) -> Neuron | None:
        key = self._key(hotkey)
        raw = await redis.hgetall(key)
        if not raw:
            return None
        data = decode_hash(raw)
        return Neuron.from_dict(data)

    async def read_all(self, redis: Redis) -> dict[str, Neuron]:
        miners: dict[str, Neuron] = {}

        async for key in redis.scan_iter(match=self._key("*")):
            decoded_key = key.decode()
            raw = await redis.hgetall(decoded_key)
            if not raw:
                continue

            ss58_address = decoded_key.split("sv:neuron:")[1]
            data = decode_hash(raw)
            miners[ss58_address] = Neuron.from_dict(data)

        return miners

    async def write(self, redis: Redis, hotkey: str, neuron: Neuron):
        key = self._key(hotkey)
        data = Neuron.to_dict(neuron)
        await redis.hmset(key, data)

    async def write_all(self, redis: Redis, neurons: list[Neuron]):
        async with redis.pipeline() as pipe:
            for neuron in neurons:
                key = self._key(neuron.hotkey)
                data = Neuron.to_dict(neuron)
                pipe.hmset(key, data)
            await pipe.execute()

    async def delete(self, redis: Redis, neuron: Neuron):
        key = self._key(neuron.hotkey)
        await redis.delete(key)

    async def delete_all(self, redis: Redis, neurons: list[Neuron]):
        async with redis.pipeline() as pipe:
            for neuron in neurons:
                key = self._key(neuron.hotkey)
                pipe.delete(key)
            await pipe.execute()
