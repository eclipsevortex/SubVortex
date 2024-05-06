import bittensor as bt
from os import path

from subnet.version.utils import get_migrations, get_migration_module
from subnet.validator.database import get_version as _get_version

here = path.abspath(path.dirname(__file__))


class Redis:
    def __init__(self, database):
        self.database = database

    async def get_version(self):
        version = await _get_version(self.database)
        return version

    def get_latest_version(self):
        migration = get_migrations(True)
        return migration[0][1] if len(migration) > 0 else None

    async def rollout(self, from_version: str, to_version: str):
        """
        Rollout from from_version to to_version
        """
        upper_version = int(to_version.replace(".", ""))
        lower_version = int(from_version.replace(".", ""))

        # List all the migration to execute
        migration_scripts = get_migrations()
        migrations = [
            x
            for x in migration_scripts
            if x[0] > lower_version and x[0] <= upper_version
        ]
        migrations = sorted(migrations, key=lambda x: x[0])

        version = None
        try:
            for migration in migrations:
                version = migration[1]

                # Load the migration module
                module = get_migration_module(migration[2])
                if not module:
                    bt.logging.error(
                        f"[Redis] Could not found the migration file {migration[2]}"
                    )
                    return

                # Rollout the migration
                await module.rollout(self.database)

                # Update the version in the database
                new_version = await self.get_version()
                if new_version:
                    bt.logging.success(f"[Redis] Rollout to {new_version} successful")
                else:
                    bt.logging.success(f"[Redis] Rollout successful")

                return True
        except Exception as err:
            bt.logging.error(f"[Redis] Failed to upgrade to {version}: {err}")

        return False

    async def rollback(self, from_version: str, to_version: str = "0.0.0"):
        upper_version = int(from_version.replace(".", ""))
        lower_version = int(to_version.replace(".", ""))

        # List all the migration to execute
        migration_scripts = get_migrations()
        migrations = [
            x
            for x in migration_scripts
            if x[0] > lower_version and x[0] <= upper_version
        ]
        migrations = sorted(migrations, key=lambda x: x[0])

        version = None
        try:
            for migration in migrations:
                version = migration[1]

                # Load the migration module
                module = get_migration_module(migration[2])
                if not module:
                    bt.logging.error(
                        f"[Redis] Could not found the migration file {migration[2]}"
                    )
                    return

                # Rollback the migration
                await module.rollback(self.database)

                # Update the version in the database
                new_version = await self.get_version()
                if new_version:
                    bt.logging.success(f"[Redis] Rollback to {new_version} successful")
                else:
                    bt.logging.success(f"[Redis] Rollback successful")

            return True
        except Exception as err:
            bt.logging.error(f"[Redis] Failed to downgrade to {version}: {err}")

        return False
