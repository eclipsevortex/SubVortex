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
