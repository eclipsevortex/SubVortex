import os
import json
import argparse
import bittensor.core.config as btcc
import bittensor.core.subtensor as btcs
import bittensor.core.metagraph as btcm
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw


class Neuron:
    def __init__(self, config):
        self.config = config

        btul.logging.info("loading subtensor")
        self.subtensor = btcs.Subtensor(config=config)
        btul.logging.info(str(self.subtensor))

        btul.logging.info("get current block")
        self.current_block = self.subtensor.get_current_block()
        btul.logging.info(f"Current block: {self.current_block}")

        btul.logging.info("loading metagraph")
        self.metagraph = btcm.Metagraph(
            netuid=self.config.netuid, network=self.subtensor.network, sync=False
        )
        self.metagraph.sync(subtensor=self.subtensor)
        btul.logging.info(str(self.metagraph))

    def run(self):
        ips_blocked = []

        # Reload the previous ips blocked
        if not os.path.exists("ips_blocked.json"):
            btul.logging.warning("No ips blocked to show")
            return

        btul.logging.debug("Loading blocked ips")
        with open("ips_blocked.json", "r") as file:
            ips_blocked = json.load(file) or []

        for details in ips_blocked:
            ip = details.get("ip")
            port = details.get("port")
            reason = details.get("reason")
            metadata = details.get("metadata") or {}
            synapse = metadata.get("synapse") or {}
            hotkey = synapse.get("hotkey")

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
                btul.logging.warning(f"[{hotkey}] {ip}:{port} is part of SN{self.config.netuid} (UID: {uid}) - {reason}")
            else:
                btul.logging.info(f"[{hotkey}] {ip}:{port} not part of SN{self.config.netuid} - {reason}")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        btcs.Subtensor.add_args(parser)
        btul.logging.add_args(parser)
        btw.Wallet.add_args(parser)
        parser.add_argument(
            "--netuid", type=int, help="Subvortex network netuid", default=7
        )
        config = btcc.Config(parser)
        btul.logging(config=config, debug=True)

        Neuron(config=config).run()
    except KeyboardInterrupt:
        btul.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        btul.logging.error(f"The configuration file is incorrect: {e}")
