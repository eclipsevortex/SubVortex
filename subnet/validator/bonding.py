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

import math
import asyncio
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
    adjusted_standard_deviation = math.sqrt(
        (p * (1 - p) + z**2 / (4 * total)) / total
    )

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


async def reset_storage_stats(stats_key: str, database: aioredis.Redis):
    """
    Asynchronously resets the storage statistics for a miner.

    This function should be called periodically to reset the statistics for a miner while keeping the tier and total_successes.

    Args:
        ss58_address (str): The unique address (hotkey) of the miner.
        database (redis.Redis): The Redis client instance for database operations.
    """
    stats = await database.hgetall(stats_key)
    tier = stats.get(b"tier", b"Bronze").decode()
    # Set min wilson score for each tier to preserve tier and can drop/go up from there based on future behavior
    if tier == "Super Saiyan":
        await database.hmset(
            stats_key,
            {
                "store_attempts": 7,
                "store_successes": 7,
                "challenge_successes": 8,
                "challenge_attempts": 8,
                "retrieve_successes": 8,
                "retrieve_attempts": 8,
            },
        )
    elif tier == "Diamond":
        await database.hmset(
            stats_key,
            {
                "store_attempts": 3,
                "store_successes": 3,
                "challenge_successes": 3,
                "challenge_attempts": 3,
                "retrieve_successes": 3,
                "retrieve_attempts": 3,
            },
        )
    elif tier == "Gold":
        await database.hmset(
            stats_key,
            {
                "store_attempts": 2,
                "store_successes": 2,
                "challenge_successes": 2,
                "challenge_attempts": 2,
                "retrieve_successes": 1,
                "retrieve_attempts": 1,
            },
        )
    elif tier == "Silver":
        await database.hmset(
            stats_key,
            {
                "store_attempts": 1,
                "store_successes": 1,
                "challenge_successes": 1,
                "challenge_attempts": 1,
                "retrieve_successes": 0,
                "retrieve_attempts": 0,
            },
        )
    else:  # Bronze
        await database.hmset(
            stats_key,
            {
                "store_attempts": 0,
                "store_successes": 0,
                "challenge_successes": 0,
                "challenge_attempts": 0,
                "retrieve_successes": 0,
                "retrieve_attempts": 0,
            },
        )


async def rollover_storage_stats(database: aioredis.Redis):
    """
    Asynchronously resets the storage statistics for all miners.
    This function should be called periodically to reset the statistics for all miners.
    Args:
        database (redis.Redis): The Redis client instance for database operations.
    """
    miner_stats_keys = [stats_key async for stats_key in database.scan_iter("stats:*")]
    tasks = [reset_storage_stats(stats_key, database) for stats_key in miner_stats_keys]
    await asyncio.gather(*tasks)


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
            "subtensor_successes": 0,
            "subtensor_attempts": 0,
            "metric_successes": 0,
            "metric_attempts": 0,
            "total_successes": 0,
            "tier": "Bronze",
        },
    )


async def update_statistics(
    ss58_address: str, success: bool, task_type: str, database: aioredis.Redis
):
    """
    Updates the statistics of a miner in the decentralized storage system.
    If the miner is not already registered, they are registered first. This function updates
    the miner's statistics based on the task performed (store, challenge, retrieve) and whether
    it was successful.
    Args:
        ss58_address (str): The unique address (hotkey) of the miner.
        success (bool): Indicates whether the task was successful or not.
        task_type (str): The type of task performed ('store', 'challenge', 'retrieve').
        database (redis.Redis): The Redis client instance for database operations.
    """
    # Check and see if this miner is registered.
    if not await miner_is_registered(ss58_address, database):
        bt.logging.debug(f"Registering new miner {ss58_address}...")
        await register_miner(ss58_address, database)

    # Update statistics in the stats hash
    stats_key = f"stats:{ss58_address}"

    if task_type in ["challenge"]:
        await database.hincrby(stats_key, f"{task_type}_attempts", 1)
        if success:
            await database.hincrby(stats_key, f"{task_type}_successes", 1)

    # Update the total successes that we rollover every epoch
    if await database.hget(stats_key, "total_successes") is None:
        subtensor_successes = int(await database.hget(stats_key, "subtensor_successes"))
        metric_successes = int(await database.hget(stats_key, "metric_successes"))
        total_successes = subtensor_successes + metric_successes
        await database.hset(stats_key, "total_successes", total_successes)
    if success:
        await database.hincrby(stats_key, "total_successes", 1)


async def compute_tier(stats_key: str, database: aioredis.Redis):
    if not await database.exists(stats_key):
        bt.logging.warning(f"Miner key {stats_key} is not registered!")
        return

    # Retrieve statistics from the database
    subtensor_successes = int(
        await database.hget(stats_key, "subtensor_successes") or 0
    )
    subtensor_attempts = int(await database.hget(stats_key, "subtensor_attempts") or 0)
    metric_successes = int(await database.hget(stats_key, "metric_successes") or 0)
    metric_attempts = int(await database.hget(stats_key, "metric_attempts") or 0)
    total_successes = int(await database.hget(stats_key, "total_successes") or 0)

    total_current_attempts = subtensor_attempts + metric_attempts
    total_current_successes = subtensor_successes + metric_successes

    # Compute the overall success rate across all tasks
    current_wilson_score = wilson_score_interval(
        total_current_successes, total_current_attempts
    )
    bt.logging.trace(
        f"Miner {stats_key} current total success rate: {current_wilson_score}"
    )

    # 

    # Use the lower bounds of the intervals to determine the tier
    if (
        current_wilson_score >= SUPER_SAIYAN_WILSON_SCORE
        and total_successes >= SUPER_SAIYAN_TIER_TOTAL_SUCCESSES
    ):
        bt.logging.trace(f"Setting {stats_key} to Super Saiyan tier.")
        tier = "Super Saiyan"
    elif (
        current_wilson_score >= DIAMOND_WILSON_SCORE
        and total_successes >= DIAMOND_TIER_TOTAL_SUCCESSES
    ):
        bt.logging.trace(f"Setting {stats_key} to Diamond tier.")
        tier = "Diamond"
    elif (
        current_wilson_score >= GOLD_WILSON_SCORE
        and total_successes >= GOLD_TIER_TOTAL_SUCCESSES
    ):
        bt.logging.trace(f"Setting {stats_key} to Gold tier.")
        tier = "Gold"
    elif (
        current_wilson_score >= SILVER_WILSON_SCORE
        and total_successes >= SILVER_TIER_TOTAL_SUCCESSES
    ):
        bt.logging.trace(f"Setting {stats_key} to Silver tier.")
        tier = "Silver"
    else:
        bt.logging.trace(f"Setting {stats_key} to Bronze tier.")
        tier = "Bronze"

    # Update the tier in the database
    await database.hset(stats_key, "tier", tier)


async def compute_all_tiers(database: aioredis.Redis):
    # Iterate over all miners
    """
    Asynchronously computes and updates the tiers for all miners in the decentralized storage system.
    This function should be called periodically to ensure miners' tiers are up-to-date based on
    their performance. It iterates over all miners and calls `compute_tier` for each one.
    Args:
        database (redis.Redis): The Redis client instance for database operations.
    """
    miners = [miner async for miner in database.scan_iter("stats:*")]
    tasks = [compute_tier(miner, database) for miner in miners]
    await asyncio.gather(*tasks)

    # Reset the statistics for the next epoch
    bt.logging.info("Resetting statistics for all hotkeys...")
    await rollover_storage_stats(database)


async def get_tier_factor(ss58_address: str, database: aioredis.Redis):
    """
    Retrieves the reward factor based on the tier of a given miner.
    This function returns a factor that represents the proportion of rewards a miner
    is eligible to receive based on their tier.
    Args:
        ss58_address (str): The unique address (hotkey) of the miner.
        database (redis.Redis): The Redis client instance for database operations.
    Returns:
        float: The reward factor corresponding to the miner's tier.
    """
    tier = await database.hget(f"stats:{ss58_address}", "tier")
    if tier == b"Super Saiyan":
        return SUPER_SAIYAN_TIER_REWARD_FACTOR
    elif tier == b"Diamond":
        return DIAMOND_TIER_REWARD_FACTOR
    elif tier == b"Gold":
        return GOLD_TIER_REWARD_FACTOR
    elif tier == b"Silver":
        return SILVER_TIER_REWARD_FACTOR
    else:
        return BRONZE_TIER_REWARD_FACTOR
