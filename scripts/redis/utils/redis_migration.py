import asyncio
import argparse
import importlib
import bittensor.utils.btlogging as btul
from redis import asyncio as aioredis

from subnet.shared.utils import get_redis_password


def get_migration(version):
    file_path = f"scripts/redis/migrations/migration-{version}.py"
    spec = importlib.util.spec_from_file_location("migration_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def rollout(args):
    try:
        btul.logging.info(
            f"Loading database from {args.database_host}:{args.database_port}"
        )
        redis_password = get_redis_password(args.redis_password)
        database = aioredis.StrictRedis(
            host=args.database_host,
            port=args.database_port,
            db=args.database_index,
            password=redis_password,
        )

        btul.logging.info("Rollout starting")

        # Get the migration
        migration = get_migration(args.version)
        if not migration:
            btul.logging.error(f"Could not find the migration {args.version}")
            return

        # Rollback the migration
        await migration.rollout(database)

        btul.logging.success("Rollout successful")
    except Exception as e:
        btul.logging.error(f"Error during rollout: {e}")


async def rollback(args):
    try:
        btul.logging.info(
            f"Loading database from {args.database_host}:{args.database_port}"
        )
        redis_password = get_redis_password(args.redis_password)
        database = aioredis.StrictRedis(
            host=args.database_host,
            port=args.database_port,
            db=args.database_index,
            password=redis_password,
        )

        btul.logging.info("Rollback starting")

        # Get the migration
        migration = get_migration(args.version)
        if not migration:
            btul.logging.error(f"Could not find the migration {args.version}")
            return

        # Rollback the migration
        await migration.rollback(database)

        btul.logging.success("Rollback successful")

    except Exception as e:
        btul.logging.error(f"Error during rollback: {e}")


async def main(args):
    if not args.version:
        btul.logging.error(f"Version is not provided")
        return

    if args.run_type == "rollout":
        await rollout(args)
    else:
        await rollback(args)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--run-type",
            type=str,
            default="rollout",
            help="Type of migration you want too execute. Possible values are rollout or rollback)",
        )
        parser.add_argument(
            "--version",
            type=str,
            help="Verstion to run",
        )
        parser.add_argument(
            "--redis_password",
            type=str,
            default=None,
            help="password for the redis database",
        )
        parser.add_argument(
            "--redis_conf_path",
            type=str,
            default="/etc/redis/redis.conf",
            help="path to the redis configuration file",
        )
        parser.add_argument("--database_host", type=str, default="localhost")
        parser.add_argument("--database_port", type=int, default=6379)
        parser.add_argument("--database_index", type=int, default=1)
        args = parser.parse_args()

        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except ValueError as e:
        print(f"ValueError: {e}")
