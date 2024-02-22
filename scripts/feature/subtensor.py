import argparse
import asyncio
import aioredis
import bittensor as bt

from subnet.shared.utils import get_redis_password


async def main(args):
    bt.logging.info(f"loading database")
    redis_password = get_redis_password(args.redis_password)
    database = aioredis.StrictRedis(
        host=args.database_host,
        port=args.database_port,
        db=args.database_index,
        password=redis_password,
    )
    
    subtensors = await database.keys(f"subs:{args.coldkey}:{args.hotkey}")
    for subtensor in subtensors:
        details = subtensor.decode('utf-8').split(':')
        hotkey = details[2]

        ip = await database.hget(subtensor, "ip")
        ip = ip.decode('utf-8')

        country = await database.hget(subtensor, "country")
        country = country.decode('utf-8')

        region = await database.hget(subtensor, "region")
        region = region.decode('utf-8')

        city = await database.hget(subtensor, "city")
        city = city.decode('utf-8')

        download = await database.hget(subtensor, "download")
        download = download.decode('utf-8')

        upload = await database.hget(subtensor, "upload")
        upload = upload.decode('utf-8')

        latency = await database.hget(subtensor, "latency")
        latency = latency.decode('utf-8')

        process_time = await database.hget(subtensor, "process_time")

        bt.logging.info(f"[{hotkey}]Subtensor hosted on {ip} ({country}, {region}, {city})")
        bt.logging.info(f"[{hotkey}][Metric] Bandwidth - Download {float(download)} Mbps / Upload {float(upload)} Mbps")
        bt.logging.info(f"[{hotkey}][Metric] Latency {float(latency)} Mbps")
        bt.logging.info(f"[{hotkey}][Metric] Challenge avg time {float(process_time)} ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--coldkey", type=str, required=True)
    parser.add_argument("--hotkey", type=str, required=False, default="*")

    # database 
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