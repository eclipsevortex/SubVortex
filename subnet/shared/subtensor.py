import sys
import time
from math import floor
from functools import lru_cache, update_wrapper
from typing import Callable, Any, List
import bittensor as bt
from bittensor.extrinsics.serving import get_metadata, MetadataError


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


def retrieve_metadata(self, hotkey: str):
    metadata = get_metadata(self.subtensor, self.config.netuid, hotkey)
    if not metadata:
        return None, None

    commitment = metadata["info"]["fields"][0]
    hex_data = commitment[list(commitment.keys())[0]][2:]
    return (bytes.fromhex(hex_data).decode(), int(metadata["block"]))


def publish_metadata(self, retry_delay_secs: int = 60):
    # We can only commit to the chain every 20 minutes, so run this in a loop, until
    # successful.
    while True:
        try:
            subtensor: bt.subtensor = None
            self.subtensor.commit(
                self.wallet, self.config.netuid, self.axon.external_ip
            )
          
            bt.logging.info(
                "Wrote metadata to the chain. Checking we can read it back..."
            )

            metadata = retrieve_metadata(self, self.wallet.hotkey.ss58_address)
           
            if not metadata or metadata[0] != self.axon.external_ip:
                bt.logging.error(
                    f"Failed to read back metadata from the chain. Expected: {self.axon.external_ip}, got: {metadata[0]}"
                )
                raise ValueError(
                    f"Failed to read back metadata from the chain. Expected: {self.axon.external_ip}, got: {metadata[0]}"
                )

            bt.logging.success("Committed metadata to the chain.")
            break
        except (MetadataError, Exception) as e:
            bt.logging.error(f"Failed to send metadata on the chain: {e}")
            bt.logging.error(f"Retrying in {retry_delay_secs} seconds...")
            time.sleep(retry_delay_secs)

def get_min_block(ip: str, metadata: List[tuple]):
    # Get all metadata with the same ip
    metadata = [x for x in metadata if x[1] == ip]

    # Get the minimum block
    min_block = sys.maxsize
    if len(metadata) > 0:
        min_block = min([x[2] for x in metadata])

    return min_block