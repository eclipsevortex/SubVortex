from typing import List, Dict
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
    neurons: Dict[str, Neuron],
    miners: List[Miner],
    validator: Neuron,
    locations: List[str],
) -> List[Miner]:
    miners_updates: List[Miner] = []

    # Resync the miners
    for hotkey, neuron in neurons.items():
        # Get the associated miner
        current_miner = next((x for x in miners if x.uid == neuron.uid), None)

        # Check if the miner is a new one (happen when there are still empty uids)
        if current_miner is None:
            # Create the new miner
            current_miner = Miner.create_new_miner(
                uid=neuron.uid,
            )

            # Log the success
            btul.logging.info(
                f"[{current_miner.uid}] New miner discovered (hotkey: {hotkey}, country: {neuron.country}, IP: {neuron.ip}). Miner added to sync list."
            )

        # Check if the miner has changed its hotkey
        elif current_miner.hotkey != hotkey:
            btul.logging.info(
                f"[{current_miner.uid}] Hotkey change detected: old={current_miner.hotkey}, new={hotkey}. This may indicate key rotation or a new node replacing the old one."
            )

            # Remove the old miner
            await database.remove_miner(miner=current_miner)

            # Reset the updated miner
            current_miner.reset()

            # Log the success
            btul.logging.debug(
                f"[{current_miner.uid}] Miner replaced due to hotkey change. State reset for syncing."
            )

        # Check if the miner has changed its ip
        elif current_miner.ip != neuron.ip:
            btul.logging.info(
                f"[{current_miner.uid}] IP address changed from {current_miner.ip} to {neuron.ip}. This may indicate redeployment or failover."
            )

            # Reset the updated miner
            current_miner.reset()

            btul.logging.debug(
                f"[{current_miner.uid}] Miner replaced due to IP change. State reset for syncing."
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

        # Add the updated miner in the list
        miners_updates.append(miner)

    # Define the ip occurences
    ip_occurrences = Counter(neuron.ip for neuron in neurons.values())

    # Recompute the miners scores
    for miner in miners_updates:
        has_ip_conflicts = ip_occurrences.get(miner.ip, 0) > 1

        # Cache old scores
        old_scores = {
            "score": miner.score,
            "availability_score": miner.availability_score,
            "reliability_score": miner.reliability_score,
            "latency_score": miner.latency_score,
            "distribution_score": miner.distribution_score,
            "challenge_successes": miner.challenge_successes,
            "challenge_attempts": miner.challenge_attempts,
        }

        # Recalculate scores
        new_availability = compute_availability_score(miner, has_ip_conflicts)
        new_latency = compute_latency_score(
            validator.country, miner, miners, locations, has_ip_conflicts
        )
        new_distribution = compute_distribution_score(miner, miners, ip_occurrences)
        new_score = compute_final_score(miner)

        # Apply new scores
        miner.availability_score = new_availability
        miner.latency_score = new_latency
        miner.distribution_score = new_distribution
        miner.score = new_score

        # Detect actual changes
        updated_scores = {
            "score": new_score,
            "availability_score": new_availability,
            "reliability_score": miner.reliability_score,
            "latency_score": new_latency,
            "distribution_score": new_distribution,
            "challenge_successes": miner.challenge_successes,
            "challenge_attempts": miner.challenge_attempts,
        }

        changed = [
            f"{key}: {old_scores[key]:.2f} → {updated_scores[key]:.2f}"
            for key in updated_scores
            if old_scores[key] != updated_scores[key]
        ]

        if changed:
            btul.logging.debug(f"[{miner.uid}] Score changes: " + ", ".join(changed))

    btul.logging.info(
        f"✅ sync_miners complete: {len(miners_updates)} miners synced from {len(neurons)} live neurons."
    )

    return miners_updates


async def reset_reliability_score(database: Database, miners: List[Miner]):
    btul.logging.info("reset_reliability_score() reset reliability statistics.")

    for miner in miners:
        miner.challenge_attempts = 0
        miner.challenge_successes = 0

    await database.update_miners(miners=miners)
