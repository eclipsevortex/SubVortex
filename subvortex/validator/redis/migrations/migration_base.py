import os
from redis import asyncio as aioredis
from dotenv import load_dotenv
from abc import ABC, abstractmethod

# Resolve the path two levels up from the current file
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../.env"))

# Load the env file
load_dotenv(dotenv_path=env_path)


class RedisMigration(ABC):
    revision: str
    down_revision: str | None

    def __init__(self):
        # Promote class attributes to instance attributes
        self.revision = type(self).revision
        self.down_revision = type(self).down_revision

        # Create the instance of redis
        self.database = aioredis.StrictRedis(
            host=os.getenv("SUBVORTEX_REDIS_HOST", "localhost"),
            port=os.getenv("SUBVORTEX_REDIS_PORT", 6379),
            db=os.getenv("SUBVORTEX_REDIS_INDEX", 0),
            password=os.getenv("SUBVORTEX_REDIS_PASSWORD"),
        )

    async def rollout(self):
        # Set mode to dual so app reads/writes both if needed
        await self.database.set(f"migration_mode:{self.revision}", "dual")

        await self._rollout()

        # Set mode to dual so app reads/writes both if needed
        await self.database.set("version", self.revision)
        await self.database.set(f"migration_mode:{self.revision}", "new")

    async def rollback(self):
        # Set mode to dual so app reads/writes both if needed
        await self.database.set(f"migration_mode:{self.revision}", "dual")

        await self._rollback()

        # Set mode to dual so app reads/writes both if needed
        if self.down_revision is not None:
            await self.database.set("version", self.down_revision)
            await self.database.set(f"migration_mode:{self.revision}", "legacy")
        else:
            await self.database.set("version", "0.0.0")
            

    @abstractmethod
    def _rollout(self):
        pass

    @abstractmethod
    def _rollback(self):
        pass
