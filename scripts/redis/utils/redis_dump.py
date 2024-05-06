import asyncio
import argparse
import bittensor as bt
from redis import asyncio as aioredis

from subnet.shared.utils import get_redis_password
from subnet.validator.database import create_dump, restore_dump


async def create(args):
    try:
        bt.logging.info(
            f"Loading database from {args.database_host}:{args.database_port}"
        )
        redis_password = get_redis_password(args.redis_password)
        database = aioredis.StrictRedis(
            host=args.database_host,
            port=args.database_port,
            db=args.database_index,
            password=redis_password,
        )

        bt.logging.info("Create dump starting")

        await create_dump(args.dump_path, database)

        bt.logging.success("Create dump successful")
    except Exception as e:
        bt.logging.error(f"Error during rollout: {e}")


async def restore(args):
    try:
        bt.logging.info(
            f"Loading database from {args.database_host}:{args.database_port}"
        )
        redis_password = get_redis_password(args.redis_password)
        database = aioredis.StrictRedis(
            host=args.database_host,
            port=args.database_port,
            db=args.database_index,
            password=redis_password,
        )

        bt.logging.info("Restore dump starting")

        await restore_dump(args.dump_path, database)

        bt.logging.success("Restore dump successful")

    except Exception as e:
        bt.logging.error(f"Error during rollback: {e}")


async def main(args):
    if args.run_type == "create":
        await create(args)
    else:
        await restore(args)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--run-type",
            type=str,
            default="create",
            help="Type of migration you want too execute. Possible values are rollout or rollback)",
        )
        parser.add_argument(
            "--dump-path",
            type=str,
            default="",
            help="Dump file (with path) to create or restore",
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
