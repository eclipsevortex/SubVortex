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
import random as pyrandom
import bittensor.utils.btlogging as btul
from typing import List

from subvortex.core.constants import DEFAULT_CHUNK_SIZE
from subvortex.core.core_bittensor.subtensor import get_block_seed


def get_available_uids(self, exclude: list = []):
    available_uids = []
    for miner in self.miners:
        if miner.ip == "0.0.0.0" or miner.uid in exclude:
            continue
        
        available_uids.append(miner.uid)
    btul.logging.debug(f"returning available uids: {available_uids}")
    return available_uids


def get_pseudorandom_uids(self, uids, k):
    block_seed = get_block_seed(subtensor=self.subtensor)
    pyrandom.seed(block_seed)

    # Ensure k is not larger than the number of uids
    k = min(k, len(uids))

    sampled = pyrandom.sample(uids, k=k)
    btul.logging.debug(f"get_pseudorandom_uids() sampled: {k} | {sampled}")
    return sampled


def get_available_query_miners(self, k, exclude: List[int] = []):
    # Determine miner axons to query from metagraph with pseudorandom block_hash seed
    muids = get_available_uids(self, exclude=exclude)
    btul.logging.debug(f"get_available_query_miners() available uids: {muids}")
    return get_pseudorandom_uids(self, muids, k=k)


async def get_next_uids(self, ss58_address: str, k: int = DEFAULT_CHUNK_SIZE):
    # Get the list of uids already selected
    # uids_already_selected = await get_selected_miners(ss58_address, self.database)
    uids_already_selected = await self.database.get_selected_miners(ss58_address)
    btul.logging.debug(
        f"get_next_uids() uids already selected: {uids_already_selected}"
    )

    # Get the list of available uids
    uids_selected = get_available_query_miners(self, k=k, exclude=uids_already_selected)

    # If no uids available we start again
    if len(uids_selected) < k:
        uids_already_selected = []
        btul.logging.debug(f"get_next_uids() not enough uids selected: {uids_selected}")

        # Complete the selection with k - len(uids_selected) elements
        # We always to have k miners selected
        new_uids_selected = get_available_query_miners(self, k=k, exclude=uids_selected)
        new_uids_selected = new_uids_selected[: k - len(uids_selected)]
        btul.logging.debug(f"get_next_uids() extra uids selected: {new_uids_selected}")

        uids_selected = uids_selected + new_uids_selected

    btul.logging.debug(f"get_next_uids() uids selected: {uids_selected}")

    # Store the new selection in the database
    selection = uids_already_selected + uids_selected
    await self.database.set_selection_miners(ss58_address, selection)
    # await set_selection(ss58_address, selection, self.database)
    btul.logging.debug(f"get_next_uids() new uids selection stored: {selection}")

    return uids_selected
