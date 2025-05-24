import typing

import subvortex.core.scheduler.utils as scsu
import subvortex.core.scheduler.models as scsm


def get_next_cycle(
    settings: scsm.Settings, netuid: int, block: int, counter: typing.Dict[str, int]
) -> range:
    """
    Compute the next cycle from the block
    """
    # Create a counter
    counter = dict(counter)

    # Get the number of blocks needed for a cycle
    cycle_blocks = len(counter) * scsu.get_step_blocks(
        settings=settings, counter=counter
    )

    # Get the cycle of the current block
    cycle = get_epoch_containing_block(
        block=block, netuid=netuid, tempo=cycle_blocks, adjust=0
    )

    return cycle


def get_epoch_containing_block(
    block: int, netuid: int, tempo: int = 360, adjust: int = 1
) -> range:
    """
    Get the current epoch of the block
    """
    assert tempo > 0

    interval = tempo + adjust
    last_epoch = block - adjust - (block + netuid + adjust) % interval
    next_tempo_block_start = last_epoch + interval
    return range(last_epoch, next_tempo_block_start)
