import time
import bittensor as bt
from math import floor
from functools import lru_cache, update_wrapper
from typing import Callable, Any


def _ttl_hash_gen(seconds: int):
    start_time = time.time()
    while 1:
        yield floor((time.time() - start_time) / seconds)


# LRU Cache with TTL
def ttl_cache(maxsize: int = 128, typed: bool = False, ttl: int = -1):
    if ttl <= 0:
        ttl = 65536
    hash_gen = _ttl_hash_gen(ttl)

    def wrapper(func: Callable) -> Callable:
        @lru_cache(maxsize, typed)
        def ttl_func(ttl_hash, *args, **kwargs):
            return func(*args, **kwargs)

        def wrapped(*args, **kwargs) -> Any:
            th = next(hash_gen)
            return ttl_func(th, *args, **kwargs)

        return update_wrapper(wrapped, func)

    return wrapper


# 12 seconds updating block.
@ttl_cache(maxsize=1, ttl=12)
def get_current_block(subtensor) -> int:
    return subtensor.get_current_block()


def get_hyperparameter_value(subtensor: "bt.subtensor", param_name: str):
    """
    Get the value of the requested hyperparameter
    """
    hex_bytes_result = subtensor.query_runtime_api(
        runtime_api="SubnetInfoRuntimeApi", method="get_subnet_hyperparams", params=[7]
    )

    if hex_bytes_result is None:
        return []

    if hex_bytes_result.startswith("0x"):
        bytes_result = bytes.fromhex(hex_bytes_result[2:])
    else:
        bytes_result = bytes.fromhex(hex_bytes_result)

    # Print the bytes object
    subnet = bt.chain_data.SubnetHyperparameters.from_vec_u8(bytes_result)
    value = subnet.__dict__[param_name]
    return value
