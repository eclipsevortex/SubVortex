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
import zlib
import time
import json
import base64
import typing
import random
import netaddr
import asyncio
import numpy as np
from typing import Optional
from itertools import cycle
from functools import partial
from numpy.typing import NDArray

import bittensor.core.config as btcc
import bittensor.core.subtensor as btcs
import bittensor.utils.btlogging as btul
import bittensor.utils.weight_utils as btuwu

import bittensor.core.async_subtensor as btcas

U16_MAX = 65535


def get_next_block(subtensor: btcs.Subtensor, block: int = 0):
    current_block = subtensor.get_current_block()

    while current_block - block < 1:
        # --- Wait for next block.
        time.sleep(1)

        current_block = subtensor.get_current_block()

    return current_block


async def get_number_of_uids(subtensor: btcas.AsyncSubtensor, netuid: int):
    """
    Return the number of UIDs in the network
    """
    # Get the number of registration during the current adjustment
    number_of_neurons = await subtensor.substrate.query(
        module="SubtensorModule",
        storage_function="SubnetworkN",
        params=[netuid],
    )

    return int(number_of_neurons.value or 0)


async def get_number_of_registration(subtensor: btcas.AsyncSubtensor, netuid: int):
    """
    Return the number of registration done in the current interval
    """
    # Get the number of registration during the current adjustment
    number_of_registration = await subtensor.substrate.query(
        module="SubtensorModule",
        storage_function="BurnRegistrationsThisInterval",
        params=[netuid],
    )

    return number_of_registration.value


async def get_max_allowed_validators(subtensor: btcas.AsyncSubtensor, netuid: int):
    """
    Return the number of registration done in the current interval
    """
    # Get the number of registration during the current adjustment
    result = await subtensor.substrate.query(
        module="SubtensorModule",
        storage_function="MaxAllowedValidators",
        params=[netuid],
    )

    return int(result.value, 0)


async def get_next_adjustment_block(subtensor: btcas.AsyncSubtensor, netuid: int):
    """
    Return the block of the next adjustment interval
    """
    # Get the adjustment interval
    adjustment_interval = await subtensor.substrate.query(
        module="SubtensorModule", storage_function="AdjustmentInterval", params=[netuid]
    )

    # Get the last adjustment interval
    last_adjustment_block = await subtensor.substrate.query(
        module="SubtensorModule",
        storage_function="LastAdjustmentBlock",
        params=[netuid],
    )

    return last_adjustment_block + adjustment_interval


async def get_axons(subtensor: btcas.AsyncSubtensor, netuid: int):
    """
    Return the list of axons
    """
    # Get the last adjustment interval
    metagraph = await subtensor.get_metagraph_info(netuid=netuid)

    axons = {}
    for idx, (axon) in enumerate(metagraph.axons):
        axon_ip = axon.get("ip", 0)
        ip = str(netaddr.IPAddress(axon_ip)) if axon_ip != 0 else "0.0.0.0"

        hotkey = metagraph.hotkeys[idx]
        axons[hotkey] = ip

    return axons


async def wait_for_block(
    subtensor: btcas.AsyncSubtensor,
    block: typing.Optional[int] = None,
    timeout: int = 24,  # Avg time of 2 blocks (1 block == 12 seconds)
):
    """
    Waits until the blockchain reaches the specified block number.

    This version watches for the time elapsed between incoming blocks
    and triggers reconnect only if no block is received within `timeout` seconds.

    Parameters:
        subtensor (AsyncReliableSubtensor): Reliable wrapper around AsyncSubtensor.
        block (Optional[int]): Target block number. If None, waits for the next one.
        timeout (int): Seconds to wait between blocks before reconnecting.

    Returns:
        bool: True if the target block was reached successfully.
    """

    attempt = 0

    while True:
        last_seen_time = time.time()
        done_event = asyncio.Event()

        try:
            # Get current block and determine the target
            current_block = await subtensor.substrate.get_block()
            current_block_hash = current_block.get("header", {}).get("hash")

            if block is not None:
                target_block = block
            else:
                target_block = current_block["header"]["number"] + 1

            btul.logging.trace(
                f"⏳ Waiting for block >= {target_block} (current: {current_block['header']['number']})",
                prefix="ReliableSubtensor",
            )

            async def handler(block_data: dict):
                nonlocal last_seen_time
                last_seen_time = time.time()

                if block_data["header"]["number"] >= target_block:
                    done_event.set()
                    return True

                return None

            async def watchdog():
                while not done_event.is_set():
                    await asyncio.sleep(1)
                    if time.time() - last_seen_time > timeout:
                        raise TimeoutError(
                            f"No block received in the last {timeout} seconds"
                        )

            btul.logging.trace(
                "🚀 Starting block subscription and watchdog.",
                prefix="ReliableSubtensor",
            )

            # Run handler + watchdog concurrently
            await asyncio.gather(
                subtensor.substrate._get_block_handler(
                    current_block_hash, header_only=True, subscription_handler=handler
                ),
                watchdog(),
            )

            return True

        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e) or repr(e)

            btul.logging.warning(
                f"🛑 wait_for_block failed (attempt {attempt + 1}): [{error_type}] {error_message}",
                prefix="ReliableSubtensor",
            )

            await subtensor.substrate._reinstantiate_substrate()

            if attempt > 0:
                # Wait avg time of a block
                btul.logging.debug(
                    "⏲️ Waiting before retrying subscription...",
                    prefix="ReliableSubtensor",
                )
                await asyncio.sleep(12)

            attempt += 1


def current_block_hash(subtensor: btcs.Subtensor):
    # Get the current block
    block = subtensor.get_current_block()

    # Get the block hash
    block_hash: str = subtensor.get_block_hash(block)
    if block_hash is not None:
        return block_hash

    return int(str(random.randint(2 << 32, 2 << 64)))


def get_block_seed(subtensor: btcs.Subtensor):
    block_hash = current_block_hash(subtensor=subtensor)
    return int(block_hash, 16)


def process_weights_for_netuid(
    uids,
    weights: np.ndarray,
    netuid: int,
    subtensor: "btcs.Subtensor",
    exclude_quantile: int = 0,
) -> tuple[NDArray[np.int64], NDArray[np.float32]]:
    btul.logging.debug("process_weights_for_netuid()")
    btul.logging.debug(f"weights: {weights}")
    btul.logging.debug(f"netuid: {netuid}")

    # Get latest metagraph from chain if metagraph is None.
    metagraph = subtensor.metagraph(netuid)

    # Cast weights to floats.
    if not isinstance(weights, np.float32):
        weights = weights.astype(np.float32)

    # Network configuration parameters from an subtensor.
    # These parameters determine the range of acceptable weights for each neuron.
    quantile = exclude_quantile / U16_MAX
    min_allowed_weights = subtensor.min_allowed_weights(netuid=netuid)
    max_weight_limit = subtensor.max_weight_limit(netuid=netuid)
    btul.logging.debug(f"quantile: {quantile}")
    btul.logging.debug(f"min_allowed_weights: {min_allowed_weights}")
    btul.logging.debug(f"max_weight_limit: {max_weight_limit}")

    # Find all non zero weights.
    non_zero_weight_idx = np.argwhere(weights > 0).squeeze(axis=1)
    non_zero_weight_uids = uids[non_zero_weight_idx]
    non_zero_weights = weights[non_zero_weight_idx]
    nzw_size = non_zero_weights.size
    if nzw_size == 0 or metagraph.n < min_allowed_weights:
        btul.logging.warning("No non-zero weights returning all ones.")
        final_weights = np.ones((metagraph.n), dtype=np.int64) / metagraph.n
        btul.logging.debug(f"final_weights: {final_weights}")
        final_weights_count = np.arange(len(final_weights))
        return final_weights_count, final_weights

    elif nzw_size < min_allowed_weights:
        btul.logging.warning(
            "No non-zero weights less then min allowed weight, returning all ones."
        )
        # ( const ): Should this be np.zeros( ( metagraph.n ) ) to reset everyone to build up weight?
        weights = np.ones((metagraph.n), dtype=np.int64) * 1e-5
        weights[non_zero_weight_idx] += non_zero_weights
        btul.logging.debug(f"final_weights: {weights}")
        normalized_weights = btuwu.normalize_max_weight(
            x=weights, limit=max_weight_limit
        )
        nw_arange = np.arange(len(normalized_weights))
        return nw_arange, normalized_weights

    btul.logging.debug(f"non_zero_weights: {non_zero_weights}")

    # Compute the exclude quantile and find the weights in the lowest quantile
    max_exclude = max(0, len(non_zero_weights) - min_allowed_weights) / len(
        non_zero_weights
    )
    exclude_quantile = min([quantile, max_exclude])
    lowest_quantile = np.quantile(non_zero_weights, exclude_quantile)
    btul.logging.debug(f"max_exclude: {max_exclude}")
    btul.logging.debug(f"exclude_quantile: {exclude_quantile}")
    btul.logging.debug(f"lowest_quantile: {lowest_quantile}")

    # Exclude all weights below the allowed quantile.
    non_zero_weight_uids = non_zero_weight_uids[lowest_quantile <= non_zero_weights]
    non_zero_weights = non_zero_weights[lowest_quantile <= non_zero_weights]
    btul.logging.debug(f"non_zero_weight_uids: {non_zero_weight_uids}")
    btul.logging.debug(f"non_zero_weights: {non_zero_weights}")

    # Normalize weights and return.
    normalized_weights = btuwu.normalize_max_weight(
        x=non_zero_weights, limit=max_weight_limit
    )
    btul.logging.debug(f"final_weights: {normalized_weights}")

    return non_zero_weight_uids, normalized_weights


def get_hyperparameter_value(subtensor: "btcs.Subtensor", param_name: str, netuid: int):
    """
    Get the value of the requested hyperparameter
    """
    hex_bytes_result = subtensor.query_runtime_api(
        runtime_api="SubnetInfoRuntimeApi",
        method="get_subnet_hyperparams",
        params=[netuid],
    )

    if hex_bytes_result is None:
        return []

    if hex_bytes_result.startswith("0x"):
        bytes_result = bytes.fromhex(hex_bytes_result[2:])
    else:
        bytes_result = bytes.fromhex(hex_bytes_result)

    # Print the bytes object
    subnet = btcc.SubnetHyperparameters.from_vec_u8(bytes_result)
    value = subnet.__dict__[param_name]
    return value


async def get_weights_min_stake(subtensor: "btcas.AsyncSubtensor"):
    """
    Return the minimum of TAO a validator need to have the set weight
    """
    # WeightsMinStake has been renamed StakeThreshold
    result = await subtensor.substrate.query(
        module="SubtensorModule", storage_function="StakeThreshold", params=[]
    )

    weight_min_stake = result.value if result is not None else 0

    # Convert Rao to Tao
    return int(float(weight_min_stake) * 10**-9)

async def get_subnet_commitments(subtensor: btcas.AsyncSubtensor, netuid: int):
    commitment = await subtensor.get_all_commitments(netuid=netuid)
    if not commitment:
        return []

    identities = {}

    for hotkey, data in commitment.items():
        try:
            # Decode data
            compressed = base64.b64decode(data)

            # Decompress data
            json_str = zlib.decompress(compressed).decode()

            identity = json.loads(json_str)
        except Exception:
            continue

        # Add the identity
        identities[hotkey] = identity

    return identities