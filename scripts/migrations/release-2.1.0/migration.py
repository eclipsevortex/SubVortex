import asyncio
import argparse
import bittensor as bt
from redis import asyncio as aioredis

from subnet.shared.utils import get_redis_password
from subnet.shared.checks import check_environment

# This migration is to clean useless keys and new ones


def check_redis(args):
    try:
        asyncio.run(check_environment(args.redis_conf_path))
    except AssertionError as e:
        bt.logging.warning(
            f"Something is missing in your environment: {e}. Please check your configuration, use the README for help, and try again."
        )


def rollout():
    bt.logging.info("No rollout")


async def rollback(args):
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

        bt.logging.info("Rollback starting")
        async for key in database.scan_iter("selection:*"):
            await database.delete(key)
        bt.logging.info("Rollback done")

        bt.logging.info("Checking rollback...")
        count = 0
        async for key in database.scan_iter("selection:*"):
            count += 1
        if count == 0:
            bt.logging.info("Check rollback successfull")
        else:
            bt.logging.error(f"Check rollback failed! You still have {count} keys to remove.")

    except Exception as e:
        bt.logging.error(f"Error during rollback: {e}")


async def main(args):
    if args.run_type == "rollout":
        rollout()
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