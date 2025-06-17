import base64
import typing
from urllib.parse import urlparse
from dataclasses import dataclass

import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.core_bittensor.subtensor.subtensor as scbtss

DEFAULT_NODE = {
    "chain": "bittensor",
    "type": "lite",
    "port": 9944,
    "max-connection": 1,
}


@dataclass
class Node:
    chain: str
    """
    Chain the node is operating in
    """

    type: str
    """
    Type of node
    """

    port: int
    """
    Port the node is acessible
    """

    max_connection: int
    """
    Max number of connection the node can proceed
    """

    @property
    def id(self) -> str:
        data = f"{self.chain}:{self.type}:{self.port}"
        return base64.urlsafe_b64encode(data.encode()).decode()


async def get_challengees_nodes(
    subtensor: btcas.AsyncSubtensor, netuid: int, inclusion: typing.List[str] = []
) -> typing.Dict[str, typing.List[Node]]:
    # Get the identities
    identities: dict = await scbtss.get_identities(subtensor=subtensor, netuid=netuid)

    nodes = {}

    for hotkey, identity in identities.items():
        if not _is_identity_correct(identity):
            continue

        if len(inclusion) > 0 and hotkey not in inclusion:
            continue

        # Load the node specification
        nodes = _load_nodes(identity)

        # Create the nodes
        for node_spec in nodes:
            # Create the node
            node = Node(
                chain=node_spec["chain"],
                type=node_spec["type"],
                port=int(node_spec["port"]),
                max_connection=int(node_spec["max_connection"]),
            )

            # Add the identity
            nodes[hotkey] = node

    return nodes

def decode_id(id: str) -> tuple[str, str, int]:
    data = base64.urlsafe_b64decode(id.encode()).decode()
    chain, type_, port = data.split(":")
    return chain, type_, int(port)

def _is_identity_correct(identity: typing.Any) -> bool:
    """Check if the identity is a dictionary with a valid 'node_manifest_url'."""
    if not isinstance(identity, dict):
        return False

    node_manifest_url = identity.get("node_manifest_url")
    if not isinstance(node_manifest_url, str):
        return False

    parsed_url = urlparse(node_manifest_url)
    if not all([parsed_url.scheme in ("http", "https"), parsed_url.netloc]):
        return False

    return True


def _load_nodes(identity: typing.Any):
    # TODO: Load the file represented by node_manifest_url and if no nodes return the following one
    return [DEFAULT_NODE]
