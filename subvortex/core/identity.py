import typing
from urllib.parse import urlparse

import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.core_bittensor.subtensor.subtensor as scbtss

DEFAULT_NODE = {
    "chain": "bittensor",
    "type": "lite",
    "port": 9944,
    "max-connection": 1,
}


async def get_challengee_identities(
    subtensor: btcas.AsyncSubtensor, netuid: int, inclusion: typing.List[str] = []
):
    # Get the identities
    identities: dict = await scbtss.get_identities(subtensor=subtensor, netuid=netuid)

    nodes = {}

    for hotkey, identity in identities.items():
        if not _is_identity_correct(identity):
            continue

        if len(inclusion) > 0 and hotkey not in inclusion:
            continue

        # Add the identity
        nodes[hotkey] = _load_node(identity)

    return nodes


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


def _load_node(identity: typing.Any):
    # TODO: Load the file represented by node_manifest_url and if no nodes return the following one
    return [DEFAULT_NODE]
