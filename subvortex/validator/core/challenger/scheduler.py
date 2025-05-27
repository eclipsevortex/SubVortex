import math
import random
import typing
import hashlib

import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as bul

import subvortex.core.model.neuron as scmn
import subvortex.validator.core.model.schedule as scms
import subvortex.validator.core.challenger.settings as sccs
import subvortex.validator.core.challenger.constants as sccc

async def get_schedules(
    substrate: btcas.AsyncSubstrateInterface,
    settings: sccs.Settings,
    cycle: range,
    validators: typing.List[scmn.Neuron],
    countries: typing.Dict[str, int],
) -> typing.Dict[str, typing.List[scms.Schedule]]:
    schedules = {}

    # Sort validators by stake
    # TODO: do we want to allowed more validators based on the number of nodes to test?
    validators = sorted(validators, key=lambda x: x.total_stake)

    # Take the best validators to cover the list of country
    validators = validators[: len(countries)]
    bul.logging.debug(f"# of challengers: {len(validators)}")

    for validator in validators:
        # Compute the miners selection the validator will have to challenge
        schedule = await get_schedule(
            substrate=substrate,
            settings=settings,
            cycle=cycle,
            validators=validators,
            countries=countries,
            hotkey=validator.hotkey,
            instance=0,
        )

        # Store the selection for the validator
        schedules[validator.uid] = schedule

    return schedules


async def get_schedule(
    substrate: btcas.AsyncSubstrateInterface,
    settings: sccs.Settings,
    cycle: range,
    validators: typing.List[scmn.Neuron],
    countries: typing.Dict[str, int],
    hotkey: str,
    instance: int,
) -> typing.List[scms.Schedule]:
    # Get the hash of the block
    block_hash = await substrate.get_block_hash(
        cycle.start - sccc.DYNAMIC_BLOCK_FINALIZATION_NUMBER
    )

    # Use the block hash as a seed
    seed = _seed(block_hash)

    # Create random instance
    rm = random.Random(seed)

    # Shuffle the validators hotkey
    rcountries = list(countries)
    rm.shuffle(rcountries)

    # Get the validator hotkeys
    ordered_hotkeys = [v.hotkey for v in validators]

    # Get the index of the current hotkey
    index = ordered_hotkeys.index(hotkey) if hotkey in ordered_hotkeys else -1
    if index == -1:
        raise Exception(
            f"Validator is not part of the 64 validators. Please stake more."
        )

    # Set the step details
    step_start = cycle.start

    # Compute the number of block needed for this step
    step_blocks = get_step_blocks(settings=settings, counter=dict(rcountries))

    steps = []
    while len(steps) < len(rcountries):
        # Get the country
        country = rcountries[(index + instance) % len(rcountries)][0]

        # Compute the end of the step
        step_end = step_start + step_blocks

        # Create the new schedule
        schedule = scms.Schedule.create(
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


def get_next_cycle(
    settings: sccs.Settings, netuid: int, block: int, countries: typing.Dict[str, int]
) -> range:
    """
    Compute the next cycle from the block
    """
    # Create a counter
    countries = dict(countries)

    # Get the number of blocks needed for a cycle
    cycle_blocks = len(countries) * get_step_blocks(settings=settings, counter=countries)

    # Get the cycle of the current block
    cycle = get_epoch_containing_block(
        block=block, netuid=netuid, tempo=cycle_blocks, adjust=0
    )

    return cycle


def get_next_step(
    settings: sccs.Settings, cycle: range, block: int, counter: typing.Dict[str, int]
):
    # Compute the number of blocks for a step
    step_blocks = get_step_blocks(settings=settings, counter=dict(counter))

    # Compute the number of steps since the cycle started (as a float)
    steps_since_start = math.ceil((block - cycle.start) / step_blocks)

    # Compute the next step
    next_step = steps_since_start + 1

    # Compute the next step
    next_step_start = cycle.start + steps_since_start * step_blocks

    return next_step, next_step_start


def get_step_blocks(settings: sccs.Settings, counter: typing.Dict[str, int]):
    """
    Compute the number of blocks to execute the longest step across all challenger
    """
    if len(counter) == 0:
        return 0

    # Compute the max challengee in the counter
    max_occurence = max([x for x in counter.values()])

    # Compute the total time to challenge all the neurons
    total_time = max_occurence * settings.max_challenge_time_per_miner

    return math.ceil(total_time / sccc.BLOCK_BUILD_TIME) + 1


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


def _seed(value):
    """Convert a large integer to a distinct 64-bit seed using SHA-256 and XOR folding."""
    hashed = hashlib.sha256(str(value).encode()).digest()
    seed = int.from_bytes(hashed[:8], "big") ^ int.from_bytes(hashed[8:16], "big")
    return seed
