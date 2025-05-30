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


async def sync_miners(
    database: Database,
    neurons: Dict[str, Neuron],
    miners: List[Miner],
    validator: Neuron,
    locations: List[str],
    min_stake: int,
) -> List[Miner]:
    miners_updates: List[Miner] = []
    reset_miners: List[Miner] = []

    # Resync the miners
    for hotkey, neuron in neurons.items():
        if (
            neuron.stake >= min_stake
            or neuron.validator_trust > 0
            or neuron.uid == validator.uid
        ):
            # It is a validator
            continue

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

            # Add the miner in the reset list
            reset_miners.append(current_miner)

            # Log the success
            btul.logging.debug(
                f"[{current_miner.uid}] Miner replaced due to hotkey change. State reset for syncing."
            )

        # Check if the miner has changed its ip
        elif current_miner.ip != neuron.ip:
            has_country_changed = current_miner.country != neuron.country

            btul.logging.info(
                f"[{current_miner.uid}] IP address changed from {current_miner.ip} to {neuron.ip}"
                + (f" Country changed: {current_miner.country} → {neuron.country}. Miner will be reset." if has_country_changed else " Country unchanged. Miner will not be reset.")
            )

            # Reset the updated miner
            current_miner.reset()

            # Add to reset list only if country changed
            if has_country_changed:
                reset_miners.append(current_miner)

            # Optional: keep or remove this debug log
            btul.logging.debug(
                f"[{current_miner.uid}] Miner reset due to IP change." + (" Country changed." if has_country_changed else "")
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

    # Remove stale miners not in the updated list
    updated_uids = {m.uid for m in miners_updates}
    previous_uids = {m.uid for m in miners}
    stale_uids = previous_uids - updated_uids

    for uid in stale_uids:
        stale_miner = next((m for m in miners if m.uid == uid), None)
        if stale_miner:
            btul.logging.info(
                f"[{stale_miner.uid}] Miner removed (hotkey: {stale_miner.hotkey}, IP: {stale_miner.ip}) — no longer eligible for sync."
            )
            await database.remove_miner(miner=stale_miner)

    # Define the ip occurences
    ip_occurrences = Counter(neuron.ip for neuron in neurons.values())

    # Recompute the miners scores
    for miner in miners_updates:
        has_ip_conflicts = ip_occurrences.get(miner.ip, 0) > 1

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

    btul.logging.info(
        f"✅ sync_miners complete: {len(miners_updates)} miners synced from {len(neurons)} live neurons."
    )

    return miners_updates, reset_miners


async def reset_reliability_score(database: Database, miners: List[Miner]):
    btul.logging.info("reset_reliability_score() reset reliability statistics.")

    for miner in miners:
        miner.challenge_attempts = 0
        miner.challenge_successes = 0

    await database.update_miners(miners=miners)
