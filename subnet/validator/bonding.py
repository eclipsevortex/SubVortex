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

import math
from typing import List
from redis import asyncio as aioredis
import bittensor as bt
from subnet.constants import *


def wilson_score_interval(successes, total):
    if total == 0:
        return 0.5  # chance

    z = 0.6744897501960817

    p = successes / total
    denominator = 1 + z**2 / total
    centre_adjusted_probability = p + z**2 / (2 * total)
    adjusted_standard_deviation = math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)

    lower_bound = (
        centre_adjusted_probability - z * adjusted_standard_deviation
    ) / denominator
    upper_bound = (
        centre_adjusted_probability + z * adjusted_standard_deviation
    ) / denominator

    wilson_score = (max(0, lower_bound) + min(upper_bound, 1)) / 2

    bt.logging.trace(
        f"Wilson score interval with {successes} / {total}: {wilson_score}"
    )
    return wilson_score


async def miner_is_registered(ss58_address: str, database: aioredis.Redis):
    """
    Checks if a miner is registered in the database.

    Parameters:
        ss58_address (str): The key representing the hotkey.
        database (redis.Redis): The Redis client instance.

    Returns:
        True if the miner is registered, False otherwise.
    """
    return await database.exists(f"stats:{ss58_address}")


async def register_miner(ss58_address: str, database: aioredis.Redis):
    """
    Registers a new miner in the decentralized storage system, initializing their statistics.
    This function creates a new entry in the database for a miner with default values,
    setting them initially to the Bronze tier and assigning the corresponding storage limit.
    Args:
        ss58_address (str): The unique address (hotkey) of the miner to be registered.
        database (redis.Redis): The Redis client instance for database operations.
    """
    # Initialize statistics for a new miner in a separate hash
    await database.hmset(
        f"stats:{ss58_address}",
        {
            "uid": -1,
            "version": "",
            "country": "",
            "verified": 0,
            "score": 0,
            "availability_score": 0,
            "latency_score": 0,
            "reliability_score": 0,
            "distribution_score": 0,
            "challenge_successes": 0,
            "challenge_attempts": 0,
            "process_time": 0,
        },
    )


async def update_statistics(
    self,
    miners: List,
):
    for miner in miners:
        # Get the hotkey
        hotkey = self.metagraph.hotkeys[miner.get("uid")]

        # Update statistics 
        await self.database.hmset(
            f"stats:{hotkey}",
            {
                "uid": miner.get("uid"),
                "version": miner.get("version"),
                "country": miner.get("country"),
                "verified": 1 if miner.get("verified") == True else 0,
                "score": miner.get("score"),
                "availability_score": miner.get("availability_score"),
                "latency_score": miner.get("latency_score"),
                "reliability_score": miner.get("reliability_score"),
                "distribution_score": miner.get("distribution_score"),
                "challenge_successes": miner.get("challenge_successes"),
                "challenge_attempts": miner.get("challenge_attempts"),
                "process_time": miner.get("process_time"),
            },
        )