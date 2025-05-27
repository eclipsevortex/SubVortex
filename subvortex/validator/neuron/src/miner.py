from typing import List
from collections import Counter

import bittensor.utils.btlogging as btul

from subvortex.validator.neuron.src.score import (
    compute_distribution_score,
    compute_availability_score,
    compute_latency_score,
    compute_final_score,
)

from subvortex.core.model.neuron import Neuron
from subvortex.validator.neuron.src.models.miner import Miner
from subvortex.validator.neuron.src.database import Database


async def get_miners(database: Database) -> List[Miner]:
    miners: List[Miner] = []

    # Get the list of neuron
    neurons = await database.get_neurons()
    if not neurons:
        return []

    for hotkey, neuron in neurons.items():
        # Get the miner
        miner = await database.get_miner(hotkey=hotkey)
        if not miner:
            # Miner does not exist in the database

            # Create an instance of miner
            miner = Miner.create_new_miner(
                uid=neuron.uid,
            )

            # Add the new miner
            await database.add_miner(miner)

        # Set the property that comes from neuron
        miner.ip = neuron.ip
        miner.port = neuron.port
        miner.coldkey = neuron.coldkey
        miner.hotkey = neuron.hotkey
        miner.country = neuron.country
        miner.axon_version = neuron.version
        miner.ip_type = neuron.ip_type
        miner.protocol = neuron.protocol
        miner.placeholder1 = neuron.placeholder1
        miner.placeholder2 = neuron.placeholder2

        # Add the new miner to the list
        miners.append(miner)

    return miners


async def sync_miners(
    database: Database,
    neurons: List[Neuron],
    miners: List[Miner],
    validator: Neuron,
    locations: List[str],
) -> List[Miner]:
    miners_updates: List[Miner] = []

    # Resync the miners
    for hotkey, neuron in neurons.items():
        # Get the associated miner
        current_miner = next((x for x in miners if x.uid == neuron.uid), None)

        # Check if the miner did not exist
        if current_miner is None:
            # Create the new miner
            current_miner = Miner.create_new_miner(
                uid=neuron.uid,
            )
        elif current_miner.hotkey != hotkey:
            # Remove the old miner
            await database.remove_miner(miner=current_miner)

            # Reset the updated miner
            current_miner.reset()

            # Log the success
            btul.logging.success(
                f"[{current_miner.uid}] New miner {hotkey} added to the list"
            )

        # Check if the miner has changed localisation
        if current_miner.ip != neuron.ip:
            btul.logging.success(
                f"[{current_miner.uid}] Miner moved from {current_miner.ip} to {neuron.ip}"
            )

        # Create an updated miner
        miner = current_miner.clone()
        miner.ip = neuron.ip
        miner.port = neuron.port
        miner.coldkey = neuron.coldkey
        miner.hotkey = neuron.hotkey
        miner.country = neuron.country
        miner.axon_version = neuron.version
        miner.ip_type = neuron.ip_type
        miner.protocol = neuron.protocol
        miner.placeholder1 = neuron.placeholder1
        miner.placeholder2 = neuron.placeholder2

        miners_updates.append(miner)

    # Define the ip occurences
    ip_occurrences = Counter(neuron.ip for neuron in neurons.values())

    # Recompute the miners scores
    for miner in miners_updates:
        # Define if miner has ip conflicts or not
        has_ip_conflicts = ip_occurrences.get(miner.ip, 0) > 1

        # Refresh the availability score
        miner.availability_score = compute_availability_score(miner, has_ip_conflicts)

        # Refresh latency score
        miner.latency_score = compute_latency_score(
            validator.country, miner, miners, locations, has_ip_conflicts
        )

        # Refresh the distribution score
        miner.distribution_score = compute_distribution_score(
            miner, miners, ip_occurrences
        )

        # Refresh the final score
        miner.score = compute_final_score(miner)

    return miners_updates


async def reset_reliability_score(database: Database, miners: List[Miner]):
    btul.logging.info("reset_reliability_score() reset reliability statistics.")

    for miner in miners:
        miner.challenge_attempts = 0
        miner.challenge_successes = 0

    await database.update_miners(miners=miners)
