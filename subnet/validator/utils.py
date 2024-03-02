# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 philanthrope

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

import torch
import bittensor as bt
import random as pyrandom
from typing import List
from Crypto.Random import random

from subnet.validator.database import hotkey_at_capacity


def remove_indices_from_tensor(tensor, indices_to_remove):
    # Sort indices in descending order to avoid index out of range error
    sorted_indices = sorted(indices_to_remove, reverse=True)
    for index in sorted_indices:
        tensor = torch.cat([tensor[:index], tensor[index + 1 :]])
    return tensor


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


async def get_available_query_miners(
    self, k, exclude: List[int] = None, exclude_full: bool = False
):
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
    if exclude_full:
        muids_nonfull = [
            uid
            for uid in muids
            if not await hotkey_at_capacity(self.metagraph.hotkeys[uid], self.database)
        ]
        bt.logging.debug(f"available uids nonfull: {muids_nonfull}")
    return get_pseudorandom_uids(self, muids, k=k)
