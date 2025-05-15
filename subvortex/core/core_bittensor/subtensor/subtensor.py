import typing
import netaddr

import bittensor.core.async_subtensor as btcas


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
    subtensor: btcas.AsyncSubtensor, block: typing.Optional[int] = None
):
    async def handler(block_data: dict):
        if block_data["header"]["number"] >= target_block:
            return True

    current_block = await subtensor.substrate.get_block()
    current_block_hash = current_block.get("header", {}).get("hash")
    if block is not None:
        target_block = block
    else:
        target_block = current_block["header"]["number"] + 1

    await subtensor.substrate._get_block_handler(
        current_block_hash,
        header_only=True,
        finalized_only=False,
        subscription_handler=handler,
    )
    return True
