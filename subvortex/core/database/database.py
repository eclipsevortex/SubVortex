import asyncio
from redis import asyncio as aioredis
from weakref import WeakKeyDictionary
from packaging.version import parse as parse_version

import bittensor.utils.btlogging as btul

from subvortex.core.database.database_utils import decode_value


class Database:
    def __init__(self, settings):
        self.models = {}
        self.settings = settings
        self._clients = WeakKeyDictionary()

    @property
    def database(self):
        loop = asyncio.get_running_loop()
        if loop not in self._clients:
            self._clients[loop] = aioredis.StrictRedis(
                host=self.settings.database_host,
                port=self.settings.database_port,
                db=self.settings.database_index,
                password=self.settings.database_password,
                decode_responses=False,
            )

        return self._clients[loop]

    async def is_connection_alive(self) -> bool:
        try:
            pong = await self.database.ping()
            return pong is True
        except Exception as e:
            btul.logging.warning(f"Redis connection check failed: {e}")
            return False

    async def ensure_connection(self):
        if not await self.is_connection_alive():
            btul.logging.warning(
                "Reconnecting to Redis...", prefix=self.settings.logging_name
            )
            # Nothing to do: database creates a fresh one as needed

    async def wait_until_ready(self, name: str):
        await self.ensure_connection()

        message_key = self._key(f"state:{name}")
        stream_key = self._key(f"state:{name}:stream")
        last_id = "$"

        try:
            snapshot = await self.database.get(message_key)
            if snapshot and snapshot.decode() == "ready":
                btul.logging.info(
                    f"{name} is already ready (via message key)",
                    prefix=self.settings.logging_name,
                )
                return

            btul.logging.debug(
                f"Waiting on stream: {stream_key}", prefix=self.settings.logging_name
            )
            while True:
                entries = await self.database.xread({stream_key: last_id}, block=0)
                if not entries:
                    continue

                for stream_key, messages in entries:
                    btul.logging.debug(
                        f"Received stream message: {messages}",
                        prefix=self.settings.logging_name,
                    )
                    for msg_id, fields in messages:
                        state = fields.get("state".encode(), b"").decode()
                        if state == "ready":
                            btul.logging.info(
                                f"{name} is now ready (via stream)",
                                prefix=self.settings.logging_name,
                            )
                            return
                        last_id = msg_id
        except Exception as err:
            btul.logging.warning(
                f"Failed to read the state of {name}: {err}",
                prefix=self.settings.logging_name,
            )

    async def _get_migration_status(self, model_name: str):
        await self.ensure_connection()

        latest = None
        active = []

        all_versions = sorted(self.models[model_name].keys(), key=parse_version)

        for version in all_versions:
            mode = await self.database.get(f"migration_mode:{version}")
            mode = decode_value(mode)

            if mode == "new":
                latest = version
            if mode in ("dual", "new"):
                active.append(version)

        if not active:
            latest = all_versions[-1] if all_versions else None
            if latest is not None:
                active = [latest]

        return latest, active

    def _key(self, key: str):
        return f"{self.settings.key_prefix}:{key}"
