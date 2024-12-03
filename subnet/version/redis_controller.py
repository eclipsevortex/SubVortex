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
import bittensor.utils.btlogging as btul
from os import path

from subnet.version.utils import get_migrations, get_migration_module
from subnet.validator.database import get_version as _get_version

here = path.abspath(path.dirname(__file__))


class Redis:
    def __init__(self, database, dump_path: str):
        self.database = database
        self.dump_path = dump_path

    async def get_version(self):
        version = await _get_version(self.database)
        return version

    def get_latest_version(self):
        migration = get_migrations(force_new=True, reverse=True)
        return migration[0][1] if len(migration) > 0 else None

    async def rollout(self, from_version: str, to_version: str):
        """
        Rollout from from_version to to_version
        """
        upper_version = int(to_version.replace(".", ""))
        lower_version = int(from_version.replace(".", ""))

        # List all the migration to execute
        migrations = get_migrations(
            filter_lambda=lambda x: x[0] > lower_version and x[0] <= upper_version
        )

        version = None
        try:
            for migration in migrations:
                version = migration[1]

                # Load the migration module
                module = get_migration_module(migration[2])
                if not module:
                    btul.logging.error(
                        f"[Redis] Could not found the migration file {migration[2]}"
                    )
                    return

                # Rollout the migration
                await module.rollout(self.database)

                # Log to keep track
                btul.logging.debug(f"[Redis] Rollout to {version} successful")

            # Update the version in the database
            btul.logging.success(f"[Redis] Rollout to {to_version} successful")

            return True
        except Exception as err:
            btul.logging.error(f"[Redis] Failed to upgrade to {version}: {err}")

        return False

    async def rollback(self, from_version: str, to_version: str = "0.0.0"):
        upper_version = int(from_version.replace(".", ""))
        lower_version = int(to_version.replace(".", ""))

        # List all the migration to execute
        migrations = get_migrations(
            reverse=True,
            filter_lambda=lambda x: x[0] > lower_version and x[0] <= upper_version,
        )

        version = None
        try:
            for migration in migrations:
                version = migration[1]

                # Load the migration module
                module = get_migration_module(migration[2])
                if not module:
                    btul.logging.error(
                        f"[Redis] Could not found the migration file {migration[2]}"
                    )
                    return

                # Rollback the migration
                await module.rollback(self.database)

                # Log to keep track
                if version:
                    btul.logging.debug(f"[Redis] Rollback from {version} successful")
                else:
                    btul.logging.debug("[Redis] Rollback successful")

            # Update the version in the database
            btul.logging.success(f"[Redis] Rollback to {to_version} successful")

            return True
        except Exception as err:
            btul.logging.error(f"[Redis] Failed to downgrade to {version}: {err}")

        return False
