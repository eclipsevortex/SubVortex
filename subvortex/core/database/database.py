from redis import asyncio as aioredis
from packaging.version import parse as parse_version

import bittensor.utils.btlogging as btul

from subvortex.core.database.database_utils import decode_value


class Database:
    def __init__(self, settings):
        self.settings = settings
        self.database = None

    async def connect(self):
        self.database = aioredis.StrictRedis(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            db=self.settings.redis_index,
            password=self.settings.redis_password,
        )

        btul.logging.info("Connected to Redis", prefix=self.settings.logging_name)

    async def is_connection_alive(self) -> bool:
        try:
            pong = await self.database.ping()
            return pong is True
        except Exception as e:
            btul.logging.warning(f"Redis connection check failed: {e}")
            return False

    async def ensure_connection(self):
        if self.database is None or not await self.is_connection_alive():
            btul.logging.warning(
                "Reconnecting to Redis...",
                prefix=self.settings.logging_name,
            )
            await self.connect()

    async def wait_until_ready(self, name: str):
        # Ensure the connection is ip and running
        await self.ensure_connection()

        message_key = self._key(f"state:{name}")
        stream_key = self._key(f"state:{name}:stream")
        last_id = "$"

        try:
            # Step 1: check the message key first
            snapshot = await self.database.get(message_key)
            if snapshot and snapshot.decode() == "ready":
                btul.logging.info(
                    f"{name} is already ready (via message key)",
                    prefix=self.settings.logging_name,
                )
                return

            # Step 2: wait for stream messages
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
                        last_id = msg_id  # move forward
        except Exception as err:
            btul.logging.warning(
                f"Failed to read the state of {name}: {err}",
                prefix=self.settings.logging_name,
            )

    async def _get_migration_status(self, model_name: str):
        """
        Returns:
            - latest_version: the 'new' version
            - active_versions: versions marked 'dual' or 'new',
            or fallback to latest if none are active.
        """
        # Ensure the connection is ip and running
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
