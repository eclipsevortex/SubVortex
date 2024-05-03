from neurons.validator import Validator


def sync_metagraph(validator: Validator, axon_details):
    # Sync the metagraph
    validator.metagraph.sync(subtensor=validator.subtensor)

    # Refresh ip
    axons = validator.metagraph.axons
    for idx, axon in enumerate(axons):
        axon.ip = axon_details[idx]["ip"]


def add_new_miner(validator: Validator, axon_details):
    """
    Add a new miner to the metagraph
    """
    n = validator.subtensor.chain_state["SubtensorModule"]["SubnetworkN"][7][0]

    # Add new neurons
    uid = validator.subtensor.force_register_neuron(
        netuid=7,
        hotkey=f"miner-hotkey-{n}",
        coldkey="mock-coldkey",
        balance=100000,
        stake=100000,
    )

    sync_metagraph(validator, axon_details)

    return uid


def replace_old_miner(validator: Validator, axon_details, axon_detail=None):
    """
    Replace a old miner by new one
    """
    # Get the number of neurons
    n = validator.subtensor.chain_state["SubtensorModule"]["SubnetworkN"][7][0]

    # Set the max to the current number
    validator.subtensor.chain_state["SubtensorModule"]["MaxAllowedUids"][7] = {0: n}

    # Add new neurons
    uid = validator.subtensor.force_register_neuron(
        netuid=7,
        hotkey=f"miner-hotkey-{n}",
        coldkey="mock-coldkey",
        balance=100000,
        stake=100000,
    )

    axon_details[uid] = axon_detail or axon_details[uid]
    sync_metagraph(validator, axon_details)

    return uid


def move_miner(validator: Validator, axon_details, uid, axon_detail=None):
    """
    Move a miner from an ip to another one
    """
    axon_details[uid] = axon_detail or axon_details[uid]
    sync_metagraph(validator, axon_details)

    return uid


def remove_miner(validator: Validator, axon_details, uid):
    """
    Remove a miner from the metagraph
    """
    axon_details[uid]['ip'] = "0.0.0.0"

    sync_metagraph(validator, axon_details)

    return uid
