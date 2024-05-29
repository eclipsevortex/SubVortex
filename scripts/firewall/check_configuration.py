import argparse
import bittensor as bt

from subnet.shared.utils import load_json_file
from subnet.miner.firewall_models import create_rule


def main(config):
    # Load the configuration
    rules = load_json_file(config.file)

    for rule in rules:
        create_rule(rule)

    bt.logging.success("The configuration file is correct")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.logging.add_args(parser)
        parser.add_argument(
            "--file",
            type=str,
            help="Configuration file to check",
            default="firewall.json",
        )

        config = bt.config(parser)
        bt.logging(config=config, debug=True)

        main(config)
    except KeyboardInterrupt:
        bt.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        bt.logging.error(f"The configuration file is incorrect: {e}")

