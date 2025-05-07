from redis import asyncio as aioredis
from abc import ABC, abstractmethod


class RedisMigration(ABC):
    revision: str
    down_revision: str | None

    def __init__(self, database: aioredis.StrictRedis):
        self.database = database

        # Promote class attributes to instance attributes
        self.revision = type(self).revision
        self.down_revision = type(self).down_revision

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
