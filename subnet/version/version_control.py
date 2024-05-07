import asyncio
import bittensor as bt
from os import path

from subnet.version.github_controller import Github
from subnet.version.interpreter_controller import Interpreter
from subnet.version.redis_controller import Redis


class VersionControl:
    def __init__(self):
        self.github = Github()
        self.interpreter = Interpreter()
        self.redis = Redis()

    def upgrade_subnet(self):
        try:
            # Get the local version
            current_version = self.github.get_version()
            bt.logging.info(f"[Subnet] Current version: {current_version}")

            # Get the remote version
            remote_version = self.github.get_latest_version()
            bt.logging.info(f"[Subnet] Remote version: {remote_version}")

            # Check if the subnet has to be upgraded
            if current_version == remote_version:
                bt.logging.success("[Subnet] Already up to date")
                return

            bt.logging.info("[Subnet] Upgrading...")

            # Pull the branch
            self.github.get_branch()

            # Install dependencies
            self.interpreter.upgrade_dependencies()

            bt.logging.success("[Subnet] Upgrade successful")
        except Exception as err:
            bt.logging.error(f"Failed to upgrade the subnet: {err}")

    async def upgrade_redis(self):
        current_version = None
        latest_version = None
        new_version = None

        try:
            # Get the local version
            current_version = await self.redis.get_version()
            bt.logging.info(f"[Redis] Current version: {current_version}")

            # Get latest version
            latest_version = self.redis.get_latest_version()
            bt.logging.info(f"[Redis] Latest version: {latest_version}")

            # Check if the subnet has to be upgraded
            if current_version == latest_version:
                bt.logging.success("[Redis] Already up to date")
                return

            new_version = await self.redis.rollout(current_version, latest_version)
        except Exception as err:
            bt.logging.error(f"Failed to upgrade redis: {err}")

        if new_version != latest_version:
            await self.redis.rollback(new_version, current_version)
            bt.logging.success("[Redis] Rollback successful")
        else:
            bt.logging.success(f"[Redis] Upgrade to {latest_version} successful")

    def upgrade_subtensor(self):
        try:
            pass
        except Exception as err:
            bt.logging.error(f"Failed to upgrade subtensor: {err}")

    async def upgrade(self):
        try:
            # Upgrade subnet
            self.upgrade_subnet()

            # Upgrade redis
            await self.upgrade_redis()

            # Upgrade subtensor
            # self.upgrade_subtensor()
        except Exception as err:
            bt.logging.error(f"Upgrade failed: {err}")


if __name__ == "__main__":
    asyncio.run(VersionControl().upgrade())
