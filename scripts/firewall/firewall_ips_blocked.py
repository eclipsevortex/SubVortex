import os
import json
import argparse
import bittensor as bt


class Neuron:
    def __init__(self, config):
        self.config = config

        bt.logging.info("loading subtensor")
        self.subtensor = bt.subtensor(config=config)
        bt.logging.info(str(self.subtensor))

        bt.logging.info("get current block")
        self.current_block = self.subtensor.get_current_block()
        bt.logging.info(f"Current block: {self.current_block}")

        bt.logging.info("loading metagraph")
        self.metagraph = bt.metagraph(
            netuid=self.config.netuid, network=self.subtensor.network, sync=False
        )
        self.metagraph.sync(subtensor=self.subtensor)
        bt.logging.info(str(self.metagraph))

    def run(self):
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
            metadata = details.get("metadata") or {}
            hotkey = metadata.get("hotkey")

            details = next(
                (
                    (index, x)
                    for index, (x) in enumerate(self.metagraph.axons)
                    if x.ip == ip or x.hotkey == hotkey
                ),
                None,
            )
            is_neuron_part_of_subnet = details is not None
            uid = self.metagraph.uids[details[0]] if details else "NA"

            if is_neuron_part_of_subnet:
                bt.logging.warning(f"{ip}:{port} is part of SN{self.config.netuid} (UID: {uid}) - {reason}")
            else:
                bt.logging.info(f"{ip}:{port} not part of SN{self.config.netuid} - {reason}")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)
        parser.add_argument(
            "--netuid", type=int, help="Subvortex network netuid", default=7
        )
        config = bt.config(parser)
        bt.logging(config=config, debug=True)

        Neuron(config=config).run()
    except KeyboardInterrupt:
        bt.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        bt.logging.error(f"The configuration file is incorrect: {e}")
