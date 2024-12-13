import asyncio
import aioredis
import argparse
import bittensor.core.config as btcc
import bittensor.utils.btlogging as btul

from subnet.validator.version import VersionControl as ValidatorVersionControl
from subnet.miner.version import VersionControl as MinerVersionControl
from subnet.shared.utils import get_redis_password


async def main(config):
    version_control = None

    if config.neuron is None:
        btul.logging.warning(f"Provide a neuron (miner or validator) to upgrade")
        return

    # Create version control instance
    if config.neuron == "miner":
        version_control = MinerVersionControl()

        # Upgrade the neuron
        version_control.upgrade(tag=config.tag, branch=config.branch)
    else:
        # Create database
        redis_password = get_redis_password(config.database.redis_password)
        database = aioredis.StrictRedis(
            host=config.database.host,
            port=config.database.port,
            db=config.database.index,
            password=redis_password,
        )

        version_control = ValidatorVersionControl(
            database, config.database.redis_dump_path
        )

        # Upgrade the neuron
        await version_control.upgrade(tag=config.tag, branch=config.branch)



if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        btul.logging.add_args(parser)
        
        parser.add_argument(
            "--neuron",
            type=str,
            help="Neuron to upgrade (miner or validator), default miner",
            default="miner",
        )
        parser.add_argument(
            "--tag",
            type=str,
            help="Tag to pull. Used by miners/validators who do not have auto update activated",
            default=None,
        )
        parser.add_argument(
            "--branch",
            type=str,
            help="Branch to pull. Use by SubVortex team only",
            default=None,
        )

        # Redis arguments
        parser.add_argument(
            "--database.host", default="localhost", help="The host of the redis database."
        )
        parser.add_argument(
            "--database.port", default=6379, help="The port of the redis database."
        )
        parser.add_argument(
            "--database.index",
            default=1,
            help="The database number of the redis database.",
        )
        parser.add_argument(
            "--database.redis_password",
            type=str,
            default=None,
            help="The redis password.",
        )
        parser.add_argument(
            "--database.redis_conf_path",
            type=str,
            help="Redis configuration path.",
            default="/etc/redis/redis.conf",
        )
        parser.add_argument(
            "--database.redis_dump_path",
            type=str,
            help="Redis directory where to store dumps.",
            default="/etc/redis/",
        )

        config = btcc.Config(parser)
        btul.logging(config=config, debug=True)

        asyncio.run(main(config))
    except KeyboardInterrupt:
        btul.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        btul.logging.error(f"The configuration file is incorrect: {e}")
