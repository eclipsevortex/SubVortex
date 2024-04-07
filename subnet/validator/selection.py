import math
import random
from typing import List
import bittensor as bt
from redis import asyncio as aioredis

from subnet.validator.models import Miner
from subnet.validator.database import get_selected_miners


DEFAULT_CHUNK_SIZE = 10

# This file is for some wok in progress, keep it for now


# If divided by chunk make some validator not busy or empty, reequillibrate
# Challenge block can be different per validator
# Common info between validators - block, hash, list of validators
def select_uids(
    vuid: int,
    step: int,
    seed: str,
    miners: List[Miner],
    vuids: List[int],
    k=None,
):
    """
    Return the uids selection for the current block and validator
    """
    bt.logging.debug(f"select_uids() {step} {seed} {k}")

    if len(miners) == 0:
        return []

    bt.logging.debug(f"Miners available {len(miners)}: {[x.uid for x in miners]}")

    # Determinate the chunk size
    chunk_size = k or max(DEFAULT_CHUNK_SIZE, math.floor(len(miners) / len(vuids)))

    # Determine the exclusion chunk size
    exclusion_chunk_size = len(miners) - (len(vuids) * chunk_size)

    # Determine the start index to take the {exclusion_chunk_size} uids to exclude
    exclusion_start_index = (step * exclusion_chunk_size) % len(miners)
    exclusion_end_index = exclusion_start_index + exclusion_chunk_size

    # Compute the exclusion list of uids
    exclusion = (
        miners[exclusion_start_index : min(len(miners), exclusion_end_index)]
        + miners[0 : max(0, exclusion_end_index - len(miners))]
    )
    bt.logging.debug(
        f"Miners excluded from selection {len(exclusion)}: {[x.uid for x in exclusion]}"
    )

    # Initial state with block hash
    uids_random = random.Random(seed)

    # Determine the miners available for selection
    max_index = min(len(vuids) * chunk_size, len(miners))
    uids = list(set(miners) - set(exclusion))[:max_index]
    uids_random.shuffle(uids)
    bt.logging.debug(f"Miners selected {len(uids)}: {[x.uid for x in uids]}")

    # Get the uids selection at the validator position amongs the validators ones
    val_idx = next((index for index, _vuid in enumerate(vuids) if _vuid == vuid), None)
    selection = uids[chunk_size * val_idx : chunk_size * (val_idx + 1)]
    random.shuffle(selection)
    bt.logging.debug(
        f"Miners selected for validator {vuid}: {len(selection)}: {[x.uid for x in selection]}"
    )

    return [item.uid for item in selection]


# Issue: no guarantee to have a fairly selection
# How to deal with the unallocated miners
def select_uids_chunk(
    _vuid: int, block: int, miners: List[Miner], vuids: List[int], k=None
):
    # Initiate random object for the block
    random_block = random.Random(block)

    # Determinate the chunk size of the selected miners
    chunk_size = k or max(10, math.floor(len(miners) / len(vuids)))
    print(chunk_size)

    # Determine the unallocated miners as the chunk size may not be enough to cover all miners
    unallocated_uids = len(miners) % chunk_size
    unallocated_chunk_size = math.ceil(unallocated_uids / len(vuids))
    print(unallocated_chunk_size)

    # Copy the list of available miners
    current_miners = miners.copy()

    # Shuffle the miner to make it unpredictable
    random_block.shuffle(current_miners)

    # Selection the right chunk of miner for our validator
    val_idx = next((index for index, value in enumerate(vuids) if value == _vuid), None)
    selection = current_miners[chunk_size * val_idx : chunk_size * (val_idx + 1)]

    print(
        f"Miner selected {len([item.uid for item in selection])}: {[item.uid for item in selection]}"
    )

    return [item.uid for item in selection]
