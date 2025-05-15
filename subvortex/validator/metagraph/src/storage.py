import typing
import traceback
from redis import asyncio as aioredis

import bittensor.utils.btlogging as btul

import subvortex.core.metagraph.models as scmm
import subvortex.core.metagraph.metagraph_storage as scmms

import subvortex.miner.metagraph.src.settings as scms


class Storage(scmms.MetagraphStorage):
    def __init__(self, settings: scms.Settings):
        self.settings = settings

        self.client = aioredis.StrictRedis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_index,
            password=settings.redis_password,
            decode_responses=True,
        )

    async def is_redis_available(self) -> bool:
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def set_neurons(self, neurons: typing.List[scmm.Neuron]):
        try:
            async with self.client.pipeline() as pipe:
                for neuron in neurons:
                    mapping = scmm.Neuron.to_dict(neuron)
                    await pipe.hmset(self._key(f"neuron:{neuron.hotkey}"), mapping)

                await pipe.execute()

        except Exception as ex:
            btul.logging.error(
                f"Failed to set neurons: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )

    async def get_neuron(self, hotkey: str) -> typing.List[scmm.Neuron]:
        try:
            mapping = await self.client.hgetall(self._key(f"neuron:{hotkey}"))
            if mapping is None:
                btul.logging.warning(f"Neuron {hotkey} does not exist.")
                return None

            return scmm.Neuron.from_dict(mapping)

        except Exception as ex:
            btul.logging.error(
                f"Failed to get neuron: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )

        return None

    async def get_neurons(self) -> typing.List[scmm.Neuron]:
        try:
            # Get all the keys
            keys = await self.client.keys(self._key("neuron:*"))

            # Create a pipeline
            pipeline = self.client.pipeline()

            # Queue all HGETALL commands in a batch
            for key in keys:
                pipeline.hgetall(key)

            # Execute all queued commands in one go
            results = await pipeline.execute()

            # Combine keys with results
            return [scmm.Neuron.from_dict(x) for x in results]

        except Exception as ex:
            btul.logging.error(
                f"Failed to get neurons: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )

        return []

    async def delete_neurons(self, hotkeys: list[str]):
        try:
            keys = [self._key(f"neuron:{hk}") for hk in hotkeys]
            await self.client.delete(*keys)
        except Exception as ex:
            btul.logging.error(
                f"Failed to delete neurons: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )

    async def mark_as_ready(self):
        await self._set_state(state="ready")

    async def mark_as_unready(self):
        await self._set_state(state="unready")

    async def notify_state(self):
        try:
            # Get the state
            state = await self.client.get(self._key("state:metagraph"))

            # Notify the state
            await self.client.xadd("metagraph", {"state": state})
        except Exception as ex:
            btul.logging.error(
                f"Failed to get neurons: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )

    def _key(self, key: str):
        return f"{self.settings.key_prefix}:{key}"

    async def _set_state(self, state: str):
        try:
            await self.client.set(self._key("state:metagraph"), state)
        except Exception as ex:
            btul.logging.error(
                f"Failed to get neurons: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )
