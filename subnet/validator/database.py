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
import os
import json
import bittensor.utils.btlogging as btul
from redis import asyncio as aioredis


def get_field_value(value, default_value=None):
    """
    Returned the decoded value of the field
    """
    field_value = value.decode("utf-8") if isinstance(value, bytes) else value
    return field_value or default_value


async def get_hotkey_statistics(ss58_address: str, database: aioredis.Redis):
    """
    Return the stastistics metadata for the hotkey from the database
    """
    try:
        statistics = await database.hgetall(f"stats:{ss58_address}")
        if statistics is None:
            btul.logging.trace(f"No statistics metadata found in hash {ss58_address}.")
            return None

        return statistics
    except Exception as ex:
        btul.logging.error(
            f"Failed to execute get_hotkey_statistics() on {ss58_address}: {ex}"
        )

    return None


async def update_hotkey_statistics(
    ss58_address: str, mapping, database: aioredis.Redis
):
    """
    Update the stastitics key from the database
    """
    try:
        await database.hmset(f"stats:{ss58_address}", mapping)
    except Exception as ex:
        btul.logging.error(
            f"Failed to execute update_hotkey_statistics() on {ss58_address}: {ex}, {mapping}"
        )


async def remove_hotkey_stastitics(ss58_address: str, database: aioredis.Redis):
    """
    Remove the stastitics key from the database
    """
    try:
        exists = await database.exists(f"stats:{ss58_address}")
        if not exists:
            return

        await database.delete(f"stats:{ss58_address}")
    except Exception as ex:
        btul.logging.error(
            f"Failed to execute remove_hotkey_stastitics() on {ss58_address}: {ex}"
        )
        btul.logging.info("Use redis_clean_old_key.py script to clean them.")


async def get_selected_miners(ss58_address: str, database: aioredis.Redis):
    try:
        # Get the uids selection
        value = await database.get(f"selection:{ss58_address}")
        if value is None:
            btul.logging.debug(f"get_selected_miners() no uids")
            return []

        # Get the uids already selected
        uids_str = value.decode("utf-8") if isinstance(value, bytes) else value
        uids = [int(uid) for uid in uids_str.split(",")]

        return uids
    except Exception as err:
        btul.logging.error(
            f"Failed to execute get_selected_miners() on {ss58_address}: {err}"
        )

    return []


async def get_version(database: aioredis.Redis):
    """
    Get the version for the redis database
    """
    version = await database.get("version")
    return version.decode("utf-8") if version else None


async def set_selection(ss58_address: str, selection: str, database: aioredis.Redis):
    """
    Set the uids selection to avoid re-selecting them until all of them have been selected at least one
    """
    selection_key = f"selection:{ss58_address}"
    await database.set(selection_key, selection)


async def set_version(version: str, database: aioredis.Redis):
    """
    Set the current redis version
    """
    await database.set("version", version)


async def create_dump(path: str, database: aioredis.Redis):
    """
    Create a dump from the database
    """
    # Get all keys in the database
    keys = await database.keys(f"*")

    dump = {}

    # Use a pipeline to batch key type queries
    async with database.pipeline() as pipe:
        for key in keys:
            # Query key type in the pipeline
            pipe.type(key)

        # Execute the pipeline
        key_types = await pipe.execute()

    # Process key-value pairs based on key types
    for key, key_type in zip(keys, key_types):
        key_str = key.decode("utf-8")
        if key_type == b"string":
            value = await database.get(key)
            dump[key_str] = value.decode("utf-8") if value is not None else None
        elif key_type == b"hash":
            hash_data = await database.hgetall(key)
            dump[key_str] = {
                field.decode("utf-8"): value.decode("utf-8")
                for field, value in hash_data.items()
            }
        elif key_type == b"list":
            list_data = await database.lrange(key, 0, -1)
            dump[key_str] = [item.decode("utf-8") for item in list_data]
        elif key_type == b"set":
            set_data = await database.smembers(key)
            dump[key_str] = {member.decode("utf-8") for member in set_data}
        elif key_type == b"zset":
            zset_data = await database.zrange(key, 0, -1, withscores=True)
            dump[key_str] = [
                (member.decode("utf-8"), score) for member, score in zset_data
            ]

    # Get the directory path
    directory, _ = os.path.split(path)

    # Ensure the directory exists, create it if it doesn't
    os.makedirs(directory, exist_ok=True)

    # Save dump file
    with open(path, "w") as file:
        json.dump(dump, file)


async def restore_dump(path: str, database: aioredis.StrictRedis):
    """
    Restore the dump into the database
    """
    # Flush the database
    await database.flushdb()

    # Load the dump
    with open(path, "r") as file:
        json_data = file.read()

    dump = json.loads(json_data)

    for key, value in dump.items():
        # Determine the data type of the key-value pair
        if isinstance(value, bytes):
            # For string keys, set the value
            await database.set(key, value)
        elif isinstance(value, dict):
            # For hash keys, sesut all fields and values
            await database.hmset(key, value)
        elif isinstance(value, list):
            # For list keys, push all elements
            await database.lpush(key, *value)
        elif isinstance(value, set):
            # For database keys, add all members
            await database.sadd(key, *value)
        elif isinstance(value, list) and all(
            isinstance(item, tuple) and len(item) == 2 for item in value
        ):
            # For sorted set keys, add all members with scores
            await database.zadd(key, dict(value))
