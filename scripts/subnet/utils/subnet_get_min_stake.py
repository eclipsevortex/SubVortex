import argparse
import bittensor as bt
from subnet.shared.substrate import get_weights_min_stake


def main(_config):
    bt.logging.check_config(_config)
    bt.logging(config=_config, debug=True, trace=True)

    bt.logging.info(f"loading subtensor")
    subtensor = bt.subtensor(config=config)

    get_weights_min_stake(subtensor.substrate)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        parser.add_argument(
            "--netuid", type=int, help="Subvortex network netuid", default=7
        )
        config = bt.config(parser)

        main(config)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except ValueError as e:
        print(f"ValueError: {e}")
