import time
import typing
import random
import socket
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

from websockets.exceptions import (
    InvalidMessage,
    WebSocketException,
)
import bittensor.core.async_subtensor as btcas
from async_substrate_interface.errors import MaxRetriesExceeded
from async_substrate_interface.async_substrate import Websocket
from async_substrate_interface.substrate_addons import RETRY_METHODS

U16_MAX = 65535

# These are the exceptions that should trigger a retry or re-instantiation
RETRYABLE_EXCEPTIONS = (
    MaxRetriesExceeded,  # Custom fallback exhaustion
    ConnectionError,  # Socket-level connection failure
    WebSocketException,  # Covers all websocket protocol issues (includes ConnectionClosed)
    InvalidMessage,  # Specific: bad WebSocket handshake
    EOFError,  # Stream ended early (common during abrupt disconnects)
    socket.gaierror,  # DNS resolution failure
    asyncio.TimeoutError,  # Node hang or await timeout
)


class RetryAsyncSubstrate(btcas.AsyncSubstrateInterface):
    def __init__(
        self,
        url: str,
        use_remote_preset: bool = False,
        fallback_chains: Optional[list[str]] = None,
        retry_forever: bool = False,
        ss58_format: Optional[int] = None,
        type_registry: Optional[dict] = None,
        type_registry_preset: Optional[str] = None,
        chain_name: str = "",
        max_retries: int = 5,
        retry_timeout: float = 60.0,
        _mock: bool = False,
    ):
        fallback_chains = fallback_chains or []
        self.fallback_chains = (
            iter(fallback_chains)
            if not retry_forever
            else cycle(fallback_chains + [url])
        )
        self.use_remote_preset = use_remote_preset
        self.chain_name = chain_name
        self._mock = _mock
        self.retry_timeout = retry_timeout
        self.max_retries = max_retries
        super().__init__(
            url=url,
            ss58_format=ss58_format,
            type_registry=type_registry,
            use_remote_preset=use_remote_preset,
            type_registry_preset=type_registry_preset,
            chain_name=chain_name,
            _mock=_mock,
            retry_timeout=retry_timeout,
            max_retries=max_retries,
        )
        self._original_methods = {
            method: getattr(self, method) for method in RETRY_METHODS
        }
        for method in RETRY_METHODS:
            setattr(self, method, partial(self._retry, method))

    async def _reinstantiate_substrate(self, e: Optional[Exception] = None) -> None:
        next_network = next(self.fallback_chains)
        if e.__class__ == MaxRetriesExceeded:
            btul.logging.error(
                f"Max retries exceeded with {self.url}. Retrying with {next_network}."
            )
        else:
            btul.logging.error(f"Connection error. Trying again with {next_network}")
        try:
            await self.ws.shutdown()
        except AttributeError:
            pass
        except Exception as shutdown_err:
            btul.logging.debug(
                f"Ignoring error during websocket shutdown: {shutdown_err}",
            )

        if self._forgettable_task is not None:
            self._forgettable_task: asyncio.Task
            self._forgettable_task.cancel()
            try:
                await self._forgettable_task
            except asyncio.CancelledError:
                pass

        self.chain_endpoint = next_network
        self.url = next_network
        self.ws = Websocket(
            next_network,
            options={
                "max_size": self.ws_max_size,
                "write_limit": 2**16,
            },
        )
        self._initialized = False
        self._initializing = False
        await self.initialize()

    async def _retry(self, method, *args, **kwargs):
        method_ = self._original_methods[method]
        try:
            return await method_(*args, **kwargs)
        except RETRYABLE_EXCEPTIONS as e:
            try:
                await self._reinstantiate_substrate(e)
                return await method_(*args, **kwargs)
            except StopAsyncIteration:
                btul.logging.error(
                    f"Max retries exceeded with {self.url}. No more fallback chains."
                )
                raise MaxRetriesExceeded


def get_next_block(subtensor: btcs.Subtensor, block: int = 0):
    current_block = subtensor.get_current_block()

    while current_block - block < 1:
        # --- Wait for next block.
        time.sleep(1)

        current_block = subtensor.get_current_block()

    return current_block


def get_number_of_neurons(subtensor: btcs.Subtensor, netuid: int):
    """
    Return the number of registration done in the current interval
    """
    # Get the number of registration during the current adjustment
    number_of_neurons = subtensor.substrate.query(
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


async def get_axons(
    subtensor: btcas.AsyncSubtensor, netuid: int, hotkeys: typing.List[str]
):
    """
    Return the list of axons
    """
    # Build the storate key for each hotkeys
    storage_keys = [
        await subtensor.substrate.create_storage_key(
            "SubtensorModule", "Axons", [netuid, hotkey]
        )
        for hotkey in hotkeys
    ]

    # Get the last adjustment interval
    response = await subtensor.substrate.query_multi(
        storage_keys=storage_keys,
    )

    axons = {}
    for data in response:
        hotkey = data[0].params[1]
        ip = str(netaddr.IPAddress(data[1]["ip"])) if data[1] is not None else "0.0.0.0"
        axons[hotkey] = ip

    return axons


async def wait_for_block(
    subtensor: btcas.AsyncSubtensor,
    block: typing.Optional[int] = None,
    timeout: int = 60,
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

            async def watchdog():
                while not done_event.is_set():
                    await asyncio.sleep(1)
                    if time.time() - last_seen_time > timeout:
                        raise TimeoutError(
                            f"No block received in the last {timeout} seconds"
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
                delay = min(subtensor.delay * (2**attempt), subtensor.max_delay)
                await asyncio.sleep(delay)

            attempt += 1


# async def wait_for_block(
#     subtensor: btcas.AsyncSubtensor, block: typing.Optional[int] = None
# ):
#     async def handler(block_data: dict):
#         if block_data["header"]["number"] >= target_block:
#             return True
#         return None

#     current_block = await subtensor.substrate.get_block()
#     current_block_hash = current_block.get("header", {}).get("hash")
#     if block is not None:
#         target_block = block
#     else:
#         target_block = current_block["header"]["number"] + 1

#     await subtensor.substrate._get_block_handler(
#         current_block_hash, header_only=True, subscription_handler=handler
#     )
#     return True


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
