import random
import typing
import hashlib
from async_substrate_interface import AsyncSubstrateInterface

import subvortex.core.scheduler.utils as scsu
import subvortex.core.scheduler.constants as scsc
import subvortex.core.scheduler.models as scsm


async def get_schedule(
    substrate: AsyncSubstrateInterface,
    settings: scsm.Settings,
    cycle: range,
    challengers: typing.List[Neuron],
    countries: typing.Dict[str, int],
    hotkey: str,
    instance: int,
) -> typing.List[scsm.Schedule]:
    # Get the hash of the block
    block_hash = await substrate.get_block_hash(
        cycle.start - scsc.DYNAMIC_BLOCK_FINALIZATION_NUMBER
    )

    # Use the block hash as a seed
    seed = _seed(block_hash)

    # Create random instance
    rm = random.Random(seed)

    # Shuffle the validators hotkey
    rcountries = list(countries)
    rm.shuffle(rcountries)

    # Get the validator hotkeys
    ordered_hotkeys = [c.hotkey for c in challengers]

    # Get the index of the current hotkey
    index = ordered_hotkeys.index(hotkey) if hotkey in ordered_hotkeys else -1
    if index == -1:
        raise Exception(
            f"Validator is not part of the 64 validators. Please stake more."
        )

    # Set the step details
    step_start = cycle.start

    # Compute the number of block needed for this step
    step_blocks = scsu.get_step_blocks(settings=settings, counter=dict(rcountries))

    steps = []
    while len(steps) < len(rcountries):
        # Get the country
        country = rcountries[(index + instance) % len(rcountries)][0]

        # Compute the end of the step
        step_end = step_start + step_blocks

        # Create the new schedule
        schedule = scsm.Schedule.create(
            index=index,
            instance=instance,
            cycle_start=cycle.start,
            cycle_end=cycle.stop,
            block_start=step_start,
            block_end=step_end,
            country=country,
        )

        # Add the new schedules
        steps.append(schedule)

        # The end of the previous step becomes the start of the next one
        step_start = step_end

        index += 1

    return steps


def _seed(value):
    """Convert a large integer to a distinct 64-bit seed using SHA-256 and XOR folding."""
    hashed = hashlib.sha256(str(value).encode()).digest()
    seed = int.from_bytes(hashed[:8], "big") ^ int.from_bytes(hashed[8:16], "big")
    return seed
