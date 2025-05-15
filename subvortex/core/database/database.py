from redis import asyncio as aioredis

import bittensor.utils.btlogging as btul


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
                "Reconnecting to Redis...", prefix=self.settings.logging_name
            )
            await self.connect()
