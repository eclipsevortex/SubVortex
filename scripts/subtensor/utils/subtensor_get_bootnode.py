import argparse
import bittensor as bt


def main(_config):
    bt.logging.check_config(_config)
    bt.logging(config=_config, debug=True, trace=True)

    bt.logging.info(f"loading subtensor")
    subtensor = bt.subtensor(config=config)

    json_body = subtensor.substrate.rpc_request(
        method="system_localListenAddresses", params=""
    )
    bootnodes = json_body["result"]
    bootnode = next(
        (
            bootnode
            for bootnode in bootnodes
            if bootnode.startswith("/ip4") and not bootnode.startswith("/ip4/127.0.0.1")
        )
    )
    bt.logging.info(f"get_bootnode() {bootnode}")


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
