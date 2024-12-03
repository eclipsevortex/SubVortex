import argparse
import bittensor.core.config as btcc
import bittensor.utils.btlogging as btul

from subnet.shared.utils import load_json_file
from subnet.firewall.firewall_model import create_rule


def main(config):
    # Load the configuration
    rules = load_json_file(config.file)

    for rule in rules:
        create_rule(rule)

    btul.logging.success("The configuration file is correct")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        btul.logging.add_args(parser)
        parser.add_argument(
            "--file",
            type=str,
            help="Configuration file to check",
            default="firewall.json",
        )

        config = btcc.Config(parser)
        btul.logging(config=config, debug=True)

        main(config)
    except KeyboardInterrupt:
        btul.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        btul.logging.error(f"The configuration file is incorrect: {e}")

