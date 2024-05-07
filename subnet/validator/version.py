import os
import sys
import bittensor as bt

from subnet.shared.version import BaseVersionControl
from subnet.version.redis_controller import Redis
from subnet.version.utils import create_dump_migrations, remove_dump_migrations
from subnet.validator.database import (
    create_dump,
    restore_dump,
    set_version,
)

LAST_VERSION_BEFORE_AUTO_UPDATE = "2.2.0"


class VersionControl(BaseVersionControl):
    def __init__(self, database, dump_path: str):
        super().__init__()
        self.redis = Redis(database, dump_path)

    def restart(self):
        bt.logging.info(f"Restarting validator...")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    async def upgrade_redis(self):
        """
        Upgrade redis with the requested version or the latest one
        Version has to follow the format major.minor.patch
        """
        local_version = None
        remote_version = None
        is_upgrade = None
        success = False

        try:
            # Get latest version
            remote_version = self.redis.get_latest_version()
            bt.logging.info(f"[Redis] Remote version: {remote_version}")

            # Get the local version
            active_version = await self.redis.get_version()
            local_version = active_version or LAST_VERSION_BEFORE_AUTO_UPDATE
            bt.logging.info(f"[Redis] Local version: {local_version}")

            # Check if the subnet has to be upgraded
            if local_version == remote_version:
                if not active_version:
                    await set_version(remote_version, self.redis.database)

                bt.logging.success(f"[Redis] Already using {local_version}")
                return (True, local_version, remote_version)

            self.must_restart = True

            # Dump the database
            dump_path = self.redis.dump_path
            dump_name = os.path.join(dump_path, f"redis-dump-{local_version}")
            await create_dump(dump_name, self.redis.database)
            bt.logging.info(f"[Redis] Dump {dump_name} created")

            local_version_num = int(local_version.replace(".", ""))
            remote_version_num = int(remote_version.replace(".", ""))

            is_upgrade = remote_version_num > local_version_num
            if is_upgrade:
                # It is an upgrade so we have to use the new migrations directory
                remove_dump_migrations()

                success = await self.redis.rollout(local_version, remote_version)
            else:
                # It is a downgrade so we have to use the old migrations directory
                success = await self.redis.rollback(local_version, remote_version)

            if is_upgrade and not success:
                bt.logging.info(f"[Redis] Rolling back to {local_version}...")
                await self.redis.rollback(remote_version, local_version)

        except Exception as err:
            bt.logging.error(f"[Redis] Upgrade failed: {err}")
            if is_upgrade:
                bt.logging.info(f"[Redis] Rolling back to {local_version}...")
                success_rollback = await self.redis.rollback(
                    remote_version, local_version
                )
                if not success_rollback:
                    dump_path = self.redis.dump_path
                    dump_name = os.path.join(dump_path, f"redis-dump-{local_version}")
                    await restore_dump(dump_name, self.redis.database)
                    bt.logging.info(f"[Redis] Dump {dump_name} restored")

        return (success, local_version, remote_version)

    def upgrade_validator(self):
        current_version = None
        remote_version = None
        is_upgrade = None
        success = False

        try:
            # Get the remote version
            remote_version = self.github.get_latest_version()
            bt.logging.debug(f"[Subnet] Remote version: {remote_version}")

            # Get the local version
            current_version = self.github.get_version()
            bt.logging.debug(f"[Subnet] Local version: {current_version}")

            # Check if the subnet has to be upgraded
            if current_version == remote_version:
                bt.logging.success(f"[Subnet] Already using {current_version}")
                return (True, current_version, remote_version)

            self.must_restart = True

            current_version_num = int(current_version.replace(".", ""))
            remote_version_num = int(remote_version.replace(".", ""))

            is_upgrade = remote_version_num > current_version_num
            if is_upgrade:
                success = self.upgrade_subnet(remote_version)
            else:
                success = self.downgrade_subnet(remote_version)

            if is_upgrade and not success:
                bt.logging.info(f"[Subnet] Rolling back to {current_version}...")
                self.downgrade_subnet(current_version)
        except Exception as err:
            bt.logging.error(f"[Subnet] Upgrade failed: {err}")
            if is_upgrade:
                bt.logging.info(f"[Subnet] Rolling back to {current_version}...")
                self.downgrade_subnet(current_version)

        return (success, current_version, remote_version)

    async def upgrade(self):
        try:
            # Flag to stop miner activity
            self.upgrading = True

            # Create the migrations dump
            create_dump_migrations()

            # Update Subnet
            subnet_success, subnet_old_version, subnet_new_version = (
                self.upgrade_validator()
            )
            if not subnet_success:
                return self.must_restart

            # Upgrade redis
            redis_success, _, _ = await self.upgrade_redis()
            if (
                subnet_success
                and subnet_old_version != subnet_new_version
                and not redis_success
            ):
                bt.logging.info(f"[Subnet] Rolling back to {subnet_old_version}...")
                self.downgrade_subnet(subnet_old_version)

            return self.must_restart
        except Exception as ex:
            bt.logging.error(f"Could not upgrade the validator: {ex}")
        finally:
            # Remove the migrations dump
            remove_dump_migrations()

            # Unflag to resume miner activity
            self.upgrading = False
            self.must_restart = False

        return True
