import argparse
import asyncio
import aioredis
import bittensor as bt

from subnet.shared.utils import get_redis_password

NETUID = 92


async def main(config):
    try:
        bt.logging.info(f"loading subtensor")
        subtensor = bt.subtensor(config=config)

        bt.logging.debug("loading metagraph")
        metagraph = bt.metagraph(netuid=NETUID, network=subtensor.network, sync=False)
        metagraph.sync(subtensor=subtensor)

        bt.logging.info(f"loading database")
        redis_password = get_redis_password(args.redis_password)
        database = aioredis.StrictRedis(
            host=config.database_host,
            port=config.database_port,
            db=config.database_index,
            password=redis_password,
        )

        async for key in database.scan_iter("stats:*"):
            key_decoded: str =  key.decode("utf-8")
            hotkey = key_decoded.removeprefix("stats:")

            if hotkey in metagraph.hotkeys:
                continue

            await database.delete(key)
            bt.logging.info(f"Key {key_decoded} removed.")

    except Exception as e:
        bt.logging.error(f"Error during script: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    bt.subtensor.add_args(parser)
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

    asyncio.run(main(bt.config(parser)))
