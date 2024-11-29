import argparse
from websockets.sync import client as ws_client
from substrateinterface.base import SubstrateInterface
import bittensor.core.config as btcc
import bittensor.core.settings as btcse
import bittensor.utils.networking as btun
import bittensor.utils.btlogging as btul

from subnet.constants import DEFAULT_PROCESS_TIME
from subnet.shared.substrate import get_neuron_for_uid_lite


class Checker:
    def __init__(self, config):
        self.config = config

    def run(self):
        substrate = None
        verified = False
        reason = None

        # Get the neuron ip
        ip = self.config.ip or btun.get_external_ip()
        btul.logging.debug(f"Subtensor to challenge {ip}")

        # Get the details of the challenge
        netuid = self.config.netuid
        uid = self.config.uid
        block = self.config.block
        property_name = self.config.property.name
        property_value = self.config.property.value
        btul.logging.debug(
            f"Challenge created - Block: {block}, Netuid: {netuid}, Uid: {uid}: Property: {property_name}, Value: {property_value}"
        )

        # Execute the challenge
        verified, reason = self._challenge(
            ip, netuid, uid, block, property_name, property_value
        )

        # Check the challenge
        if verified:
            btul.logging.success(f"Challenge successfully")
        else:
            btul.logging.error(f"Challenge failed - {reason}")

    def _challenge(self, ip, netuid, uid, block, property_name, property_value):
        substrate = None
        verified = False
        reason = None

        try:
            # Attempt to connect to the subtensor
            try:
                # Create the websocket
                websocket = ws_client.connect(
                    f"ws://{ip}:9944",
                    open_timeout=DEFAULT_PROCESS_TIME,
                    max_size=2**32,
                )

                # Create the substrate
                substrate = SubstrateInterface(
                    ss58_format=btcse.SS58_FORMAT,
                    use_remote_preset=True,
                    type_registry=btcse.TYPE_REGISTRY,
                    websocket=websocket,
                )

            except Exception:
                reason = "Failed to connect to Subtensor node at the given IP."
                return (verified, reason)

            # Execute the challenge
            neuron = None
            try:
                neuron = get_neuron_for_uid_lite(
                    substrate=substrate, netuid=netuid, uid=uid, block=block
                )
                btul.logging.error(neuron)
            except KeyError:
                reason = "Invalid netuid or uid provided."
                return (verified, reason)
            except ValueError:
                reason = "Invalid or unavailable block number."
                return (verified, reason)
            except (Exception, BaseException):
                reason = "Failed to retrieve neuron details."
                return (verified, reason)

            # Access the specified property
            try:
                miner_value = getattr(neuron, property_name)
            except AttributeError:
                reason = "Property not found in the neuron."
                return (verified, reason)

            # Verify the challenge
            verified = property_value == f"{miner_value}"

        except Exception as err:
            reason = f"An unexpected error occurred: {str(err)}"
        finally:
            if substrate:
                substrate.close()

        return (verified, reason)


if __name__ == "__main__":
    block_handler = None
    try:
        parser = argparse.ArgumentParser()
        btul.logging.add_args(parser)

        parser.add_argument(
            "--ip", type=str, help="Ip of the miner to challenge", default=None
        )

        parser.add_argument("--netuid", type=int, help="Uid of the subnet", default=7)

        parser.add_argument("--uid", type=int, help="Uid of the neuron", default=0)

        parser.add_argument("--block", type=int, help="Block number", default=None)

        parser.add_argument(
            "--property.name",
            type=str,
            help="Name of the property in the neuro object",
            default=None,
        )

        parser.add_argument(
            "--property.value",
            type=str,
            help="Value of the property in the neuro object",
            default=None,
        )

        config = btcc.Config(parser)
        btul.logging(config=config, debug=True)
        btul.logging.set_trace(config.logging.trace)
        btul.logging._stream_formatter.set_trace(config.logging.trace)

        checker = Checker(config)
        checker.run()
    except KeyboardInterrupt:
        btul.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        btul.logging.debug(f"ValueError: {e}")
