import argparse
import bittensor as bt


def main(_config):
    bt.logging.check_config(_config)
    bt.logging(config=_config, debug=True, trace=True)

    bt.logging.info(f"loading subtensor")
    subtensor = bt.subtensor(config=config)

    json_body = subtensor.substrate.rpc_request(
        "system_localListenAddresses", params=[]
    )

    result = json_body["result"]
    print(result)
    ip = next(
        (
            bootnode
            for bootnode in result
            if bootnode.startswith("/ip4") and not bootnode.startswith("/ip4/127.0.0.1")
        ),
        None,
    )
    bt.logging.info(f"get_bootnode() {ip}")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        config = bt.config(parser)

        main(config)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except ValueError as e:
        print(f"ValueError: {e}")
