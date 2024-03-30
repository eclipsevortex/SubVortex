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

from subnet.validator.database import hotkey_at_capacity


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


async def ping_uid(self, uid):
    """
    Ping a list of UIDs to check their availability.
    Returns a tuple with a list of successful UIDs and a list of failed UIDs.
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


async def ping_uids(self, uids):
    """
    Ping a list of UIDs to check their availability.
    Returns a tuple with a list of successful UIDs and a list of failed UIDs.
    """
    axons = [self.metagraph.axons[uid] for uid in uids]
    try:
        responses = await self.dendrite(
            axons,
            bt.Synapse(),
            deserialize=False,
            timeout=5,
        )
        successful_uids = [
            uid
            for uid, response in zip(uids, responses)
            if response.dendrite.status_code == 200
        ]
        failed_uids = [
            uid
            for uid, response in zip(uids, responses)
            if response.dendrite.status_code != 200
        ]
    except Exception as e:
        bt.logging.error(f"Dendrite ping failed: {e}")
        successful_uids = []
        failed_uids = uids
    bt.logging.debug("ping() successful uids:", successful_uids)
    bt.logging.debug("ping() failed uids    :", failed_uids)
    return successful_uids, failed_uids


async def ping_and_retry_uids(
    self, k: int = 4, max_retries: int = 3, exclude_uids: List[int] = []
):
    """
    Fetch available uids to minimize waiting for timeouts if they're going to fail anyways...
    """
    # Select initial subset of miners to query
    uids = await get_available_query_miners(self, k=k, exclude=exclude_uids)
    bt.logging.debug("initial ping_and_retry() uids:", uids)

    retries = 0
    successful_uids = set()
    failed_uids = set()
    while len(successful_uids) < k and retries < max_retries:
        # Ping all UIDs
        current_successful_uids, current_failed_uids = await ping_uids(self, uids)
        successful_uids.update(current_successful_uids)
        failed_uids.update(current_failed_uids)

        bt.logging.debug(f"successful_uids: {successful_uids}")
        bt.logging.debug(f"failed_uids: {failed_uids}")

        # If enough UIDs are successful, select the first k items
        if len(successful_uids) >= k:
            uids = list(successful_uids)[:k]
            break

        # Reroll for k UIDs excluding the successful ones
        uids = await get_available_query_miners(
            self, k=k, exclude=list(successful_uids.union(failed_uids))
        )
        bt.logging.debug(f"ping_and_retry() new uids: {uids}")
        retries += 1

    # Log if the maximum retries are reached without enough successful UIDs
    if len(successful_uids) < k:
        bt.logging.warning(
            f"Insufficient successful UIDs for k: {k} Success UIDs {successful_uids} Failed UIDs: {failed_uids}"
        )

    return list(successful_uids)[:k], failed_uids


async def get_next_uids(self, ss58_address: str, k: int = 4):
    # Get the list of uids already selected
    uids_already_selected = await get_selected_miners(self, ss58_address)
    bt.logging.debug(f"get_next_uids() uids already selected: {uids_already_selected}")

    # Get the list of available uids
    uids = await get_available_query_miners(self, k=k, exclude=uids_already_selected)
    bt.logging.debug(f"get_next_uids() uids:{uids}")

    # Get the k uids requested
    uids_selected = list(set(uids) - set(uids_already_selected))

    # If no uids available we start again
    if len(uids_selected) < k:
        uids_already_selected = []
        
        # Complete the selection with k - len(uids_selected) elements 
        # We always to have k miners selected
        new_uids_selected = await get_available_query_miners(self, k=k)

        # Ensure the new_uids_selected does not contain a uid that exist in uids_selected
        # We do not want to have twice the same uid
        new_uids_selected = [uid for uid in new_uids_selected if uid not in uids_selected]

        uids_selected = uids_selected + new_uids_selected[:k - len(uids_selected)]

    bt.logging.debug(f"get_next_uids() uids selected: {uids_selected}")

    # Store the new selection in the database
    selection_key = f"selection:{ss58_address}"
    selection = ",".join(str(uid) for uid in uids_already_selected + uids_selected)
    await self.database.set(selection_key, selection)
    bt.logging.debug(f"get_next_uids() new uids selection stored: {selection}")

    return uids_selected


async def get_selected_miners(self, ss58_address: str):
    selection_key = f"selection:{ss58_address}"

    # Get the uids selection
    value = await self.database.get(selection_key)
    if value is None:
        bt.logging.debug(f"get_selected_miners() no uids")
        return []

    # Get the uids already selected
    uids_str = value.decode("utf-8") if isinstance(value, bytes) else value
    uids = [int(uid) for uid in uids_str.split(",")]

    return uids
