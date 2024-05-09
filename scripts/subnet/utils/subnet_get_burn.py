import argparse
import bittensor as bt


def main(_config):
    bt.logging.check_config(_config)
    bt.logging(config=_config, debug=True, trace=True)

    bt.logging.info(f"loading subtensor")
    subtensor = bt.subtensor(config=config)

    burn = subtensor.recycle(netuid=config.netuid)
    bt.logging.info(f"get_burn() {burn.tao}")


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
