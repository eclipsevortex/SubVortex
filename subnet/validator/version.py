# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import os
import sys
import subprocess
from os import path
import bittensor.utils.btlogging as btul

from subnet.shared.version import BaseVersionControl
from subnet.version.redis_controller import Redis
from subnet.version.utils import create_dump_migrations, remove_dump_migrations
from subnet.validator.database import (
    create_dump,
    restore_dump,
    set_version,
)

LAST_VERSION_BEFORE_AUTO_UPDATE = "2.2.0"

here = path.abspath(path.dirname(__file__))


class VersionControl(BaseVersionControl):
    def __init__(self, database, dump_path: str):
        super().__init__()
        self.redis = Redis(database, dump_path)

    def restart(self):
        btul.logging.info(f"Restarting validator...")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def update_os_packages(self):
        try:
            script_path = path.join(here, "../../scripts/os/os_setup.sh")
            result = subprocess.run(
                ["bash", script_path, "-t", "validator"],
                check=True,
                text=True,
                capture_output=True,
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as err:
            btul.logging.error(f"[OS] Upgrade failed: {err}")

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
            btul.logging.info(f"[Redis] Remote version: {remote_version}")

            # Get the local version
            active_version = await self.redis.get_version()
            local_version = active_version or LAST_VERSION_BEFORE_AUTO_UPDATE
            btul.logging.info(f"[Redis] Local version: {local_version}")

            # Check if the subnet has to be upgraded
            if local_version == remote_version:
                if not active_version:
                    await set_version(remote_version, self.redis.database)

                btul.logging.success(f"[Redis] Already using {local_version}")
                return (True, local_version, remote_version)

            self.must_restart = True

            # Dump the database
            dump_path = self.redis.dump_path
            dump_name = os.path.join(dump_path, f"redis-dump-{local_version}")
            await create_dump(dump_name, self.redis.database)
            btul.logging.info(f"[Redis] Dump {dump_name} created")

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
                btul.logging.info(f"[Redis] Rolling back to {local_version}...")
                await self.redis.rollback(remote_version, local_version)

        except Exception as err:
            btul.logging.error(f"[Redis] Upgrade failed: {err}")
            if is_upgrade:
                btul.logging.info(f"[Redis] Rolling back to {local_version}...")
                success_rollback = await self.redis.rollback(
                    remote_version, local_version
                )
                if not success_rollback:
                    dump_path = self.redis.dump_path
                    dump_name = os.path.join(dump_path, f"redis-dump-{local_version}")
                    await restore_dump(dump_name, self.redis.database)
                    btul.logging.info(f"[Redis] Dump {dump_name} restored")

        return (success, local_version, remote_version)

    def upgrade_validator(self, tag=None, branch=None):
        current_version = None
        remote_version = None
        is_upgrade = None
        success = False

        try:
            # Get the remote version
            remote_version = self.github.get_latest_version()
            btul.logging.debug(f"[Subnet] Remote version: {remote_version}")

            # Get the local version
            current_version = self.github.get_version()
            btul.logging.debug(f"[Subnet] Local version: {current_version}")

            # True if there is a custom tag or branch, false otherwise
            is_custom_version = tag is not None or branch is not None

            # Check if the subnet has to be upgraded
            if not is_custom_version and current_version == remote_version:
                btul.logging.success(f"[Subnet] Already using {current_version}")
                return (True, current_version, remote_version)

            self.must_restart = True

            current_version_num = int(current_version.replace(".", ""))
            remote_version_num = int(remote_version.replace(".", ""))

            if is_custom_version:
                success = self.upgrade_subnet(tag=tag, branch=branch)
            elif remote_version_num > current_version_num:
                success = self.upgrade_subnet(version=remote_version)
            else:
                success = self.downgrade_subnet(version=remote_version)

            if not success:
                btul.logging.info(f"[Subnet] Rolling back to {current_version}...")
                self.downgrade_subnet(current_version)
        except Exception as err:
            btul.logging.error(f"[Subnet] Upgrade failed: {err}")
            if is_upgrade:
                btul.logging.info(f"[Subnet] Rolling back to {current_version}...")
                self.downgrade_subnet(current_version)

        return (success, current_version, remote_version)

    async def upgrade(self, tag=None, branch=None):
        try:
            # Flag to stop miner activity
            self.upgrading = True

            # Create the migrations dump
            create_dump_migrations()

            # Install os packages
            self.update_os_packages()

            # Update Subnet
            subnet_success, subnet_old_version, subnet_new_version = (
                self.upgrade_validator(tag=tag, branch=branch)
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
                btul.logging.info(f"[Subnet] Rolling back to {subnet_old_version}...")
                self.downgrade_subnet(subnet_old_version)

            return self.must_restart
        except Exception as ex:
            btul.logging.error(f"Could not upgrade the validator: {ex}")
        finally:
            # Remove the migrations dump
            remove_dump_migrations()

            # Unflag to resume miner activity
            self.upgrading = False
            self.must_restart = False

        return True
