import time
import bittensor as bt

from subnet.shared.utils import get_version, version2number
from subnet.bittensor.synapse import TerminalInfo, Synapse


class SubVortexDendrite(bt.dendrite):
    def _get_endpoint_url(self, target_axon, request_name):
        """
        Constructs the endpoint URL for a network request to a target axon.

        This internal method generates the full HTTP URL for sending a request to the specified axon. The
        URL includes the IP address and port of the target axon, along with the specific request name. It
        differentiates between requests to the local system (using '0.0.0.0') and external systems.

        Args:
            target_axon: The target axon object containing IP and port information.
            request_name: The specific name of the request being made.

        Returns:
            str: A string representing the complete HTTP URL for the request.
        """
        endpoint = (
            f"0.0.0.0:{target_axon.port}"
            if target_axon.ip == str(self.external_ip)
            else f"{target_axon.ip}:{target_axon.port}"
        )
        return f"http://{endpoint}/{request_name}"

    def preprocess_synapse_for_request(
        self,
        target_axon_info: bt.AxonInfo,
        synapse: Synapse,
        timeout: float = 12.0,
    ) -> bt.Synapse:
        """
        Pre process the synapse before sending the request to the miner
        """
        # Set the timeout for the synapse
        synapse.timeout = timeout

        # Build the Dendrite headers using the local system's details
        validator_version = version2number(get_version())
        synapse.dendrite = TerminalInfo(
            ip=self.external_ip,
            version=bt.__version_as_int__,
            neuron_version=validator_version,
            nonce=time.time_ns(),
            uuid=self.uuid,
            hotkey=self.keypair.ss58_address,
        )

        # Build the Axon headers using the target axon's details
        synapse.axon = bt.TerminalInfo(
            ip=target_axon_info.ip,
            port=target_axon_info.port,
            hotkey=target_axon_info.hotkey,
        )

        # Sign the request using the dendrite, axon info, and the synapse body hash
        message = f"{synapse.dendrite.nonce}.{synapse.dendrite.hotkey}.{synapse.axon.hotkey}.{synapse.dendrite.uuid}.{synapse.body_hash}"
        synapse.dendrite.signature = f"0x{self.keypair.sign(message).hex()}"

        return synapse
