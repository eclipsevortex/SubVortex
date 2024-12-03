import argparse
import bittensor.core.config as btcc
import bittensor.core.subtensor as btcs
import bittensor.utils.btlogging as btul


def main(_config):
    btul.logging.check_config(_config)
    btul.logging(config=_config, debug=True, trace=True)

    btul.logging.info(f"loading subtensor")
    subtensor = btcs.Subtensor(config=config)

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
    btul.logging.info(f"get_bootnode() {ip}")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        btcs.Subtensor.add_args(parser)
        btul.logging.add_args(parser)
        config = btcc.Config(parser)

        main(config)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except ValueError as e:
        print(f"ValueError: {e}")
