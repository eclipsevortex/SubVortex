import math
import typing

import subvortex.core.scheduler.constants as scsc
import subvortex.core.scheduler.models as scsm

def get_step_blocks(settings: scsm.Settings, counter: typing.Dict[str, int]):
    """
    Compute the number of blocks to execute the longest step across all challenger
    """
    if len(counter) == 0:
        return 0

    # Compute the max challengee in the counter
    max_occurence = max([x for x in counter.values()])

    # Compute the total time to challenge all the neurons
    total_time = max_occurence * settings.MAX_CHALLENGE_TIME_PER_MINER

    return math.ceil(total_time / scsc.BLOCK_BUILD_TIME) + 1
