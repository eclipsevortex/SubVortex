import subvortex.validator.redis.migrations.migration_base as svrmmb


class Migration(svrmmb.RedisMigration):
    revision = "2.0.0"
    down_revision = None

    async def _rollout(self):
        async for key in self.database.scan_iter("stats:*"):
            metadata_dict = await self.database.hgetall(key)

            if b"subtensor_successes" not in metadata_dict:
                await self.database.hset(key, b"subtensor_successes", 0)
            if b"subtensor_attempts" not in metadata_dict:
                await self.database.hset(key, b"subtensor_attempts", 0)
            if b"metric_successes" not in metadata_dict:
                await self.database.hset(key, b"metric_successes", 0)
            if b"metric_attempts" not in metadata_dict:
                await self.database.hset(key, b"metric_attempts", 0)
            if b"total_successes" not in metadata_dict:
                await self.database.hset(key, b"total_successes", 0)
            if b"tier" not in metadata_dict:
                await self.database.hset(key, b"tier", "Bronze")

    async def _rollback(self):
        async for key in self.database.scan_iter("stats:*"):
            metadata_dict = await self.database.hgetall(key)

            if b"subtensor_successes" in metadata_dict:
                await self.database.hdel(key, b"subtensor_successes")
            if b"subtensor_attempts" in metadata_dict:
                await self.database.hdel(key, b"subtensor_attempts")
            if b"metric_successes" in metadata_dict:
                await self.database.hdel(key, b"metric_successes")
            if b"metric_attempts" in metadata_dict:
                await self.database.hdel(key, b"metric_attempts")
            if b"total_successes" in metadata_dict:
                await self.database.hdel(key, b"total_successes")
            if b"tier" in metadata_dict:
                await self.database.hdel(key, b"tier")
