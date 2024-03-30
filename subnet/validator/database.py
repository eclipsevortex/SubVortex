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

import json
import bittensor as bt
from typing import Any
from redis import asyncio as aioredis
from typing import Dict, Optional


async def get_metadata_for_hotkey_and_hash(
    ss58_address: str, data_hash: str, database: aioredis.Redis, verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Retrieves specific metadata from a hash in Redis for the given field_key.

    Parameters:
        ss58_address (str): The hotkey assoicated.
        data_hash (str): The data hash associated.
        databse (aioredis.Redis): The Redis client instance.

    Returns:
        The deserialized metadata as a dictionary, or None if not found.
    """
    # Get the JSON string from Redis
    metadata_json = await database.hget(f"hotkey:{ss58_address}", data_hash)
    if verbose:
        bt.logging.trace(
            f"hotkey {ss58_address[:16]} | data_hash {data_hash[:16]} | metadata_json {metadata_json}"
        )
    if metadata_json:
        # Deserialize the JSON string to a Python dictionary
        metadata = json.loads(metadata_json)
        return metadata
    else:
        bt.logging.trace(f"No metadata found for {data_hash} in hash {ss58_address}.")
        return None


async def total_hotkey_storage(
    hotkey: str, database: aioredis.Redis, verbose: bool = False
) -> int:
    """
    Calculates the total storage used by a hotkey in the database.

    Parameters:
        database (aioredis.Redis): The Redis client instance.
        hotkey (str): The key representing the hotkey.

    Returns:
        The total storage used by the hotkey in bytes.
    """
    total_storage = 0
    keys = await database.hkeys(f"hotkey:{hotkey}")
    for data_hash in keys:
        if data_hash.startswith(b"ttl:"):
            continue
        # Get the metadata for the current data hash
        metadata = await get_metadata_for_hotkey_and_hash(
            hotkey, data_hash, database, verbose
        )
        if metadata:
            # Add the size of the data to the total storage
            total_storage += metadata["size"]
    return total_storage


async def hotkey_at_capacity(
    hotkey: str, database: aioredis.Redis, verbose: bool = False
) -> bool:
    """
    Checks if the hotkey is at capacity.

    Parameters:
        database (aioredis.Redis): The Redis client instance.
        hotkey (str): The key representing the hotkey.

    Returns:
        True if the hotkey is at capacity, False otherwise.
    """
    # Get the total storage used by the hotkey
    total_storage = await total_hotkey_storage(hotkey, database, verbose)
    # Check if the hotkey is at capacity
    byte_limit = await database.hget(f"stats:{hotkey}", "storage_limit")
    if byte_limit is None:
        if verbose:
            bt.logging.trace(f"Could not find storage limit for {hotkey}.")
        return False
    try:
        limit = int(byte_limit)
    except Exception as e:
        if verbose:
            bt.logging.trace(f"Could not parse storage limit for {hotkey} | {e}.")
        return False
    if total_storage >= limit:
        if verbose:
            bt.logging.trace(
                f"Hotkey {hotkey} is at max capacity {limit // 1024**3} GB."
            )
        return True
    else:
        if verbose:
            bt.logging.trace(
                f"Hotkey {hotkey} has {(limit - total_storage) // 1024**3} GB free."
            )
        return False


async def build_miners_table(database: aioredis.Redis, metagraph: bt.metagraph):
    miners = []
    async for key in database.scan_iter("stats:*"):
        result = await database.hgetall(key)

        miner = {}
        for field, value in result.items():
            field_str = field.decode("utf-8") if isinstance(field, bytes) else field
            value_str = value.decode("utf-8") if isinstance(value, bytes) else value

            if field_str == "uid" and value_str == -1:
                idx = metagraph.hotkeys.index(key)
                value_str = metagraph.uids[idx]

            miner[field_str] = value_str

        miners.append(miner)

    return miners
