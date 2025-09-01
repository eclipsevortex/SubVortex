import asyncio
from redis import asyncio as aioredis
from packaging.version import parse as parse_version
from weakref import WeakKeyDictionary

import bittensor.utils.btlogging as btul
from subvortex.core.database.database_utils import decode_value


class Database:
    def __init__(self, settings):
        self.models = {}
        self.settings = settings
        self._clients = WeakKeyDictionary()  # Cache clients per event loop

    def _new_client(self):
        return aioredis.StrictRedis(
            host=self.settings.database_host,
            port=self.settings.database_port,
            db=self.settings.database_index,
            password=self.settings.database_password,
        )

    def _get_loop(self):
        return asyncio.get_running_loop()

    async def get_client(self):
        loop = self._get_loop()

        if loop in self._clients:
            return self._clients[loop]

        client = self._new_client()
        self._clients[loop] = client

        btul.logging.info(
            "Created new Redis client for event loop", prefix=self.settings.logging_name
        )
        
        return client

    async def is_connection_alive(self) -> bool:
        client = await self.get_client()

        try:
            pong = await client.ping()
            return pong is True
        except Exception as e:
            btul.logging.warning(
                f"Redis connection check failed: {e}", prefix=self.settings.logging_name
            )
            return False

    async def ensure_connection(self):
        retry_delay = 1.0  # Start with 1 second
        attempt = 0
        
        while True:
            attempt += 1
            
            if await self.is_connection_alive():
                # Connection is working
                if attempt > 1:
                    btul.logging.info(
                        f"✅ Redis connection restored after {attempt - 1} attempts",
                        prefix=self.settings.logging_name,
                    )
                return
                
            # Connection failed
            if attempt == 1:
                btul.logging.warning(
                    "🔄 Redis connection lost, will keep trying until restored...",
                    prefix=self.settings.logging_name,
                )
            
            # Remove broken client from cache
            loop = self._get_loop()
            if loop in self._clients:
                try:
                    await self._clients[loop].close()
                except:
                    pass  # Ignore errors when closing broken client
                del self._clients[loop]
            
            # Log every 10 attempts to avoid spam
            if attempt % 10 == 0:
                btul.logging.warning(
                    f"🔄 Redis still unreachable after {attempt} attempts, continuing...",
                    prefix=self.settings.logging_name,
                )
            else:
                btul.logging.debug(
                    f"🔄 Redis reconnection attempt {attempt} failed, retrying in {retry_delay}s...",
                    prefix=self.settings.logging_name,
                )
                
            await asyncio.sleep(retry_delay)
            # Exponential backoff with cap
            retry_delay = min(retry_delay * 1.2, 30.0)  # Cap at 30 seconds

    async def wait_until_ready(self, name: str):
        await self.ensure_connection()

        client = await self.get_client()

        message_key = self._key(f"state:{name}")
        stream_key = self._key(f"state:{name}:stream")
        last_id = "$"

        try:
            snapshot = await client.get(message_key)
            if snapshot and snapshot.decode() == "ready":
                btul.logging.debug(
                    f"{name} is already ready (via message key)",
                    prefix=self.settings.logging_name,
                )
                return

            btul.logging.debug(
                f"Waiting on stream: {stream_key}", prefix=self.settings.logging_name
            )
            while True:
                entries = await client.xread({stream_key: last_id}, block=0)
                if not entries:
                    continue

                for stream_key, messages in entries:
                    btul.logging.debug(
                        f"Received stream message: {messages}",
                        prefix=self.settings.logging_name,
                    )
                    for msg_id, fields in messages:
                        state = fields.get(b"state", b"").decode()
                        if state == "ready":
                            btul.logging.debug(
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

        client = await self.get_client()

        latest = None
        active = []

        all_versions = sorted(self.models[model_name].keys(), key=parse_version)

        for version in all_versions:
            mode = await client.get(f"migration_mode:{version}")
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
