from typing import List, Dict
from collections import defaultdict

import bittensor.utils.btlogging as btul

from subvortex.core.model.neuron import Neuron
from subvortex.validator.core.model.miner import Miner
from subvortex.validator.core.challenger.database import Database
from subvortex.validator.core.challenger.settings import Settings


async def sync_miners(
    settings: Settings,
    database: Database,
    neurons: Dict[str, Neuron],
    miners: List[Miner],
    validator: Neuron,
    min_stake: int,
) -> List[Miner]:
    next_miners: List[Miner] = []

    # Build UID → hotkeys mapping for later duplication check
    uid_to_hotkeys = defaultdict(list)
    for miner in miners:
        uid_to_hotkeys[miner.uid].append(miner.hotkey)

    # Resync the miners
    for hotkey, neuron in neurons.items():
        is_validator = (
            neuron.validator_trust > 0
            or neuron.uid == validator.uid
            or (not settings.is_test and neuron.stake >= min_stake)
        )

        if is_validator:
            # It is a validator
            btul.logging.trace(
                f"[{neuron.uid}] Skipping neuron — validator status detected "
                f"(stake: {neuron.stake}, trust: {neuron.validator_trust})"
            )

            continue

        # Get the associated miner
        current_miner = next(
            (x for x in miners if x.uid == neuron.uid or x.hotkey == neuron.hotkey),
            None,
        )

        # Check if the miner is a new one (happens when there are still empty uids)
        if current_miner is None:
            # Create the new miner
            current_miner = Miner.create_new_miner(uid=neuron.uid)

            # Log the success
            btul.logging.info(
                f"[{current_miner.uid}] New miner discovered — hotkey: {hotkey}, "
                f"country: {neuron.country}, IP: {neuron.ip}. Miner added to sync list."
            )

        # Check if the miner has changed its hotkey
        elif current_miner.hotkey != hotkey:
            btul.logging.info(
                f"[{current_miner.uid}] Hotkey change detected — old: {current_miner.hotkey}, "
                f"new: {hotkey}. Resetting miner state (possible key rotation or replacement)."
            )

            # Reset the updated miner
            current_miner.reset(True)

            # Log the success
            btul.logging.debug(
                f"[{current_miner.uid}] Miner replaced due to hotkey change. State reset for syncing."
            )

        # Check if the miner has changed its IP
        elif current_miner.ip != neuron.ip:
            has_country_changed = current_miner.country != neuron.country

            btul.logging.info(
                f"[{current_miner.uid}] IP change detected — old: {current_miner.ip}, new: {neuron.ip}. "
                + (
                    f"Country changed: {current_miner.country} → {neuron.country}. Miner will be reset."
                    if has_country_changed
                    else "Country unchanged. Miner will not be reset."
                )
            )

            # Reset the updated miner
            current_miner.reset(has_country_changed)

            # Optional: keep or remove this debug log
            btul.logging.debug(
                f"[{current_miner.uid}] Miner reset due to IP change."
                + (" Country changed." if has_country_changed else "")
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
        next_miners.append(miner)

    # Remove stale miners not in the updated list
    for miner in miners:
        match = next(
            (m for m in next_miners if m.uid == miner.uid and m.hotkey == miner.hotkey),
            None,
        )
        if match:
            continue

        # Remove the miner in the database
        await database.remove_miner(miner=miner)

        btul.logging.info(
            f"[{miner.uid}] Miner removed — hotkey: {miner.hotkey}, IP: {miner.ip}."
        )

    btul.logging.info(
        f"✅ sync_miners complete — {len(next_miners)} miners synced from {len(neurons)} live neurons."
    )

    return next_miners
