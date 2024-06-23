import os
import json
import argparse
import bittensor as bt


def main(config):
    bt.logging.info("loading subtensor")
    subtensor = bt.subtensor(config=config)
    bt.logging.info(str(subtensor))

    bt.logging.info("loading metagraph")
    metagraph = bt.metagraph(
        netuid=config.netuid, network=subtensor.network, sync=False
    )
    metagraph.sync(subtensor=subtensor)
    bt.logging.info(str(metagraph))

    ips_blocked = []

    # Reload the previous ips blocked
    if not os.path.exists("ips_blocked.json"):
        bt.logging.warning("No ips blocked to show")
        return

    bt.logging.debug("Loading blocked ips")
    with open("ips_blocked.json", "r") as file:
        ips_blocked = json.load(file) or []

    for details in ips_blocked:
        ip = details.get("ip")
        port = details.get("port")
        reason = details.get("reason")

        details = next(
            ((index, x) for index, (x) in enumerate(metagraph.axons) if x["ip"] == ip),
            None,
        )
        uid = metagraph.uids[details[0]] if details else "NA"

        message = f"[{uid}] {ip}:{port} - {reason}"
        bt.logging.info(message)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        config = bt.config(parser)
        bt.logging(config=config, debug=True)

        main(config)
    except KeyboardInterrupt:
        bt.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        bt.logging.error(f"The configuration file is incorrect: {e}")
