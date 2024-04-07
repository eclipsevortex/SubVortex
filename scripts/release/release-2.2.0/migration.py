import asyncio
import argparse
import bittensor as bt
from redis import asyncio as aioredis

from subnet.shared.utils import get_redis_password
from subnet.shared.checks import check_environment


def check_redis(args):
    try:
        asyncio.run(check_environment(args.redis_conf_path))
    except AssertionError as e:
        bt.logging.warning(
            f"Something is missing in your environment: {e}. Please check your configuration, use the README for help, and try again."
        )


async def rollout(args):
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

        bt.logging.info("Rollout starting")
        async for key in database.scan_iter("*"):
            metadata_dict = await database.hgetall(key)

            # Remove old keys that are not used
            if b"subtensor_successes" in metadata_dict:
                await database.hdel(key, b"subtensor_successes")
            if b"subtensor_attempts" in metadata_dict:
                await database.hdel(key, b"subtensor_attempts")
            if b"metric_successes" in metadata_dict:
                await database.hdel(key, b"metric_successes")
            if b"metric_attempts" in metadata_dict:
                await database.hdel(key, b"metric_attempts")
            if b"total_successes" in metadata_dict:
                await database.hdel(key, b"total_successes")
            if b"tier" in metadata_dict:
                await database.hdel(key, b"tier")

            # Add new keys
            if b"uid" not in metadata_dict:
                await database.hset(key, b"uid", -1)
            if b"version" not in metadata_dict:
                await database.hset(key, b"version", "")
            if b"country" not in metadata_dict:
                await database.hset(key, b"country", "")
            if b"verified" not in metadata_dict:
                await database.hset(key, b"verified", 0)
            if b"score" not in metadata_dict:
                await database.hset(key, b"score", 0)
            if b"availability_score" not in metadata_dict:
                await database.hset(key, b"availability_score", 0)
            if b"latency_score" not in metadata_dict:
                await database.hset(key, b"latency_score", 0)
            if b"reliability_score" not in metadata_dict:
                await database.hset(key, b"reliability_score", 0)
            if b"distribution_score" not in metadata_dict:
                await database.hset(key, b"distribution_score", 0)
            if b"challenge_successes" not in metadata_dict:
                await database.hset(key, b"challenge_successes", 0)
            if b"challenge_attempts" not in metadata_dict:
                await database.hset(key, b"challenge_attempts", 0)
            if b"process_time" not in metadata_dict:
                await database.hset(key, b"process_time", 0)
        bt.logging.info("Rollout done")

        bt.logging.info("Checking rollout...")
        checked = True
        async for key in database.scan_iter("*"):
            # Do not do anything if not a stats key
            if key.decode().startswith("stats:") == False:
                continue

            # Check stats key does contains certain properties
            hash_data = await database.hgetall(key)

            properties_added = [
                "uid",
                "version",
                "country",
                "verified",
                "score",
                "availability_score",
                "latency_score",
                "reliability_score",
                "distribution_score",
                "process_time",
                "challenge_successes",
                "challenge_attempts",
            ]

            keys = [
                prop
                for prop in properties_added
                if f"b{prop}" not in hash_data.keys()
            ]

            diff = list(set(properties_added) - set(keys))
            if len(diff) > 0:
                bt.logging.warning(f"Some stats key(s) {diff} have not been created.")
                checked = False
                break

        if checked:
            bt.logging.info("Rollout checked successfully")
    except Exception as e:
        bt.logging.error(f"Error during rollout: {e}")


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
        # Remove uids selection key
        async for key in database.scan_iter("selection:*"):
            await database.delete(key)

        # Remove uid stats keys
        async for key in database.scan_iter("*"):
            metadata_dict = await database.hgetall(key)

            # Remove keys
            if b"uid" in metadata_dict:
                await database.hdel(key, b"uid")
            if b"version" in metadata_dict:
                await database.hdel(key, b"version")
            if b"country" in metadata_dict:
                await database.hdel(key, b"country")
            if b"verified" in metadata_dict:
                await database.hdel(key, b"verified")
            if b"score" in metadata_dict:
                await database.hdel(key, b"score")
            if b"availability_score" in metadata_dict:
                await database.hdel(key, b"availability_score")
            if b"latency_score" in metadata_dict:
                await database.hdel(key, b"latency_score")
            if b"reliability_score" in metadata_dict:
                await database.hdel(key, b"reliability_score")
            if b"distribution_score" in metadata_dict:
                await database.hdel(key, b"distribution_score")
            if b"process_time" in metadata_dict:
                await database.hdel(key, b"process_time")

            # Add keys
            if b"challenge_successes" not in metadata_dict:
                await database.hset(key, b"challenge_successes", 0)
            if b"challenge_attempts" not in metadata_dict:
                await database.hset(key, b"challenge_attempts", 0)
        bt.logging.info("Rollback done")

        bt.logging.info("Checking rollback...")
        checked = True
        async for key in database.scan_iter("*"):
            # Check selection key has been removed
            if key.decode().startswith("selection:"):
                checked = False
                bt.logging.warning(f"The selection key {key} still exist.")
                break

            # Do not do anything if not a stats key
            if key.decode().startswith("stats:"):
                continue

            # Check stats key does contains certain properties
            hash_data = await database.hgetall(key)

            properties_removed = [
                "uid",
                "version",
                "country",
                "verified",
                "score",
                "availability_score",
                "latency_score",
                "reliability_score",
                "distribution_score",
                "process_time",
            ]

            keys = [
                prop
                for prop in properties_removed
                if prop.encode() not in hash_data.keys()
            ]

            diff = list(set(properties_removed) - set(keys))
            if len(keys) > 0:
                bt.logging.warning(f"The stats key(s) {diff} still exist.")
                checked = False
                break

            properties_added = [
                "challenge_successes",
                "challenge_attempts",
            ]

            keys = [
                prop
                for prop in properties_added
                if f"b{prop}" not in hash_data.keys()
            ]

            diff = list(set(properties_added) - set(keys))
            if len(keys) > 0:
                bt.logging.warning(f"The stats key(s) {diff} does not exist.")
                checked = False
                break

        if checked:
            bt.logging.info("Rollback checked successfully")

    except Exception as e:
        bt.logging.error(f"Error during rollback: {e}")


async def main(args):
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