import argparse
import bittensor as bt

from subnet.validator.version import VersionControl as ValidatorVersionControl
from subnet.miner.version import VersionControl as MinerVersionControl


def main(config):
    version_control = None

    if config.neuron is None:
        bt.logging.warning(f"Provide a neuron (miner or validator) to upgrade")
        return

    # Create version control instance
    if config.neuron == "miner":
        version_control = MinerVersionControl()
    else:
        version_control = ValidatorVersionControl(config.database.redis_dump_path)

    # Upgrade the neuron
    version_control.upgrade(tag=config.tag, branch=config.branch)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.logging.add_args(parser)
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

        parser.add_argument(
            "--database.redis_dump_path",
            type=str,
            help="Redis directory where to store dumps.",
            default="/etc/redis/",
        )

        config = bt.config(parser)
        bt.logging(config=config, debug=True)

        main(config)
    except KeyboardInterrupt:
        bt.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        bt.logging.error(f"The configuration file is incorrect: {e}")
