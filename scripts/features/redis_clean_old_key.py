import argparse
import asyncio
import aioredis
import bittensor.core.config as btcc
import bittensor.core.subtensor as btcs
import bittensor.core.metagraph as btcm
import bittensor.utils.btlogging as btul

from subnet.shared.utils import get_redis_password

NETUID = 92


async def main(config):
    try:
        btul.logging.info(f"loading subtensor")
        subtensor = btcs.Subtensor(config=config)

        btul.logging.debug("loading metagraph")
        metagraph = btcm.Metagraph(netuid=NETUID, network=subtensor.network, sync=False)
        metagraph.sync(subtensor=subtensor)

        btul.logging.info(f"loading database")
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
            btul.logging.info(f"Key {key_decoded} removed.")

    except Exception as e:
        btul.logging.error(f"Error during script: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    btcs.Subtensor.add_args(parser)
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

    asyncio.run(main(btcc.Config(parser)))
