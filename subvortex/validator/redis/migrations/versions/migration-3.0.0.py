import subvortex.validator.redis.migrations.migration_base as svrmmb


class Migration(svrmmb.RedisMigration):
    revision = "3.0.0"
    down_revision = "2.3.0"

    async def _rollout(self):
        await self.database.set("newkey", 0)

    async def _rollback(self):
       await self.database.delete("newkey")
