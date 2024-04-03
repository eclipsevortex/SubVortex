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
            bt.logging.trace(f"No statistics metadata found in hash {ss58_address}.")
            return None

        return statistics
    except Exception as ex:
        bt.logging.error(f"Failed to execute get_hotkey_statistics(): {ex}")

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
        bt.logging.error(f"Failed to execute update_hotkey_statistics(): {ex}")

    return None


async def remove_hotkey_stastitics(ss58_address: str, database: aioredis.Redis):
    """
    Remove the stastitics key from the database
    """
    try:
        if not database.exists(f"stats:{ss58_address}"):
            return

        await database.hdel(f"stats:{ss58_address}")
    except Exception as ex:
        bt.logging.error(f"Failed to execute remove_hotkey_stastitics(): {ex}")
        bt.logging.info("Use redis_clean_old_key.py script to clean them.")
