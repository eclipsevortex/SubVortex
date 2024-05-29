# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import bittensor as bt
import random as pyrandom
from typing import List
from Crypto.Random import random

from subnet.constants import DEFAULT_CHUNK_SIZE
from subnet.validator.models import Miner
from subnet.validator.database import get_selected_miners, set_selection


def current_block_hash(self):
    """
    Get the current block hash with caching.

    Args:
        subtensor (bittensor.subtensor.Subtensor): The subtensor instance to use for getting the current block hash.

    Returns:
        str: The current block hash.
    """
    try:
        block_hash: str = self.subtensor.get_block_hash(
            self.subtensor.get_current_block()
        )
        if block_hash is not None:
            return block_hash
    except Exception as e:
        bt.logging.warning(
            f"Failed to get block hash: {e}. Returning a random hash value."
        )
    return int(str(random.randint(2 << 32, 2 << 64)))


def check_uid_availability(
    metagraph: "bt.metagraph.Metagraph", uid: int, vpermit_tao_limit: int
) -> bool:
    """Check if uid is available. The UID should be available if it is serving and has less than vpermit_tao_limit stake
    Args:
        metagraph (:obj: bt.metagraph.Metagraph): Metagraph object
        uid (int): uid to be checked
        vpermit_tao_limit (int): Validator permit tao limit
    Returns:
        bool: True if uid is available, False otherwise
    """
    # Filter non serving axons.
    if not metagraph.axons[uid].is_serving:
        return False
    # Filter validator permit > 1024 stake.
    if metagraph.validator_permit[uid]:
        if metagraph.S[uid] > vpermit_tao_limit:
            return False
    # Available otherwise.
    return True


def get_block_seed(self):
    """
    Get the block seed for the current block.

    Args:
        subtensor (bittensor.subtensor.Subtensor): The subtensor instance to use for getting the block seed.

    Returns:
        int: The block seed.
    """
    block_hash = current_block_hash(self)
    bt.logging.trace(f"block hash in get_block_seed: {block_hash}")
    return int(block_hash, 16)


def get_available_uids(self, exclude: list = None):
    """Returns all available uids from the metagraph.

    Returns:
        uids (torch.LongTensor): All available uids.
    """
    avail_uids = []

    for uid in range(self.metagraph.n.item()):
        uid_is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        if uid_is_available and (exclude is None or uid not in exclude):
            avail_uids.append(uid)
    bt.logging.debug(f"returning available uids: {avail_uids}")
    return avail_uids


def get_pseudorandom_uids(self, uids, k):
    """
    Get a list of pseudorandom uids from the given list of uids.

    Args:
        subtensor (bittensor.subtensor.Subtensor): The subtensor instance to use for getting the block_seed.
        uids (list): The list of uids to generate pseudorandom uids from.

    Returns:
        list: A list of pseudorandom uids.
    """
    block_seed = get_block_seed(self)
    pyrandom.seed(block_seed)

    # Ensure k is not larger than the number of uids
    k = min(k, len(uids))

    sampled = pyrandom.sample(uids, k=k)
    bt.logging.debug(f"get_pseudorandom_uids() sampled: {k} | {sampled}")
    return sampled


def get_available_query_miners(self, k, exclude: List[int] = None):
    """
    Obtain a list of available miner UIDs selected pseudorandomly based on the current block hash.

    Args:
        k (int): The number of available miner UIDs to retrieve.

    Returns:
        list: A list of pseudorandomly selected available miner UIDs.
    """
    # Determine miner axons to query from metagraph with pseudorandom block_hash seed
    muids = get_available_uids(self, exclude=exclude)
    bt.logging.debug(f"get_available_query_miners() available uids: {muids}")
    return get_pseudorandom_uids(self, muids, k=k)


async def ping_uid(self, uid):
    """
    Ping a UID to check their availability.
    Returns True if successful, false otherwise
    """
    try:
        response = await self.dendrite(
            self.metagraph.axons[uid],
            bt.Synapse(),
            deserialize=False,
            timeout=5,
        )

        return response.dendrite.status_code == 200
    except Exception as e:
        bt.logging.error(f"Dendrite ping failed: {e}")

    return False


async def get_next_uids(self, ss58_address: str, k: int = DEFAULT_CHUNK_SIZE):
    # Get the list of uids already selected
    uids_already_selected = await get_selected_miners(ss58_address, self.database)
    bt.logging.debug(f"get_next_uids() uids already selected: {uids_already_selected}")

    # Get the list of available uids
    uids_selected = get_available_query_miners(self, k=k, exclude=uids_already_selected)

    # If no uids available we start again
    if len(uids_selected) < k:
        uids_already_selected = []
        bt.logging.debug(f"get_next_uids() not enough uids selected: {uids_selected}")

        # Complete the selection with k - len(uids_selected) elements
        # We always to have k miners selected
        new_uids_selected = get_available_query_miners(self, k=k, exclude=uids_selected)
        new_uids_selected = new_uids_selected[: k - len(uids_selected)]
        bt.logging.debug(f"get_next_uids() extra uids selected: {new_uids_selected}")

        uids_selected = uids_selected + new_uids_selected

    bt.logging.debug(f"get_next_uids() uids selected: {uids_selected}")

    # Store the new selection in the database
    selection = ",".join(str(uid) for uid in uids_already_selected + uids_selected)
    await set_selection(ss58_address, selection, self.database)
    bt.logging.debug(f"get_next_uids() new uids selection stored: {selection}")

    return uids_selected


def deregister_suspicious_uid(miners: List[Miner], moving_averaged_scores):
    """
    Deregister all miners that are either
    - suspicious from the load balancer
    - does not own their subtensor
    """
    for miner in miners:
        if not miner.suspicious:
            continue

        # Set the weight to 0 on the chain if there is no penalise factor
        # Set the weight to penalise factor if provided
        penalty_factor = miner.penalty_factor or 0
        moving_averaged_scores[miner.uid] = (
            moving_averaged_scores[miner.uid] * penalty_factor
        )
