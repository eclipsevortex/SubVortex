import bittensor as bt
from typing import List

from subnet.validator.models import Miner
from subnet.validator.score import (
    compute_distribution_score,
    compute_availability_score,
    compute_latency_score,
    compute_final_score,
)
from subnet.validator.utils import get_available_uids, check_uid_availability
from subnet.validator.localisation import get_country
from subnet.validator.database import (
    get_hotkey_statistics,
    remove_hotkey_stastitics,
    get_field_value,
    update_hotkey_statistics,
)


def get_miner_ip_occurences(ip: str, ips: List[str]):
    """
    Return the number of miners using the same ip
    """
    count = sum(1 for item in ips if item == ip)
    return count or 1


async def get_all_miners(self) -> List[Miner]:
    """
    Load the miners stored in the database
    """
    miners: List[Miner] = []

    ips = [axon.ip for axon in self.metagraph.axons]

    uids = get_available_uids(self)
    for uid in uids:
        axon = self.metagraph.axons[uid]

        # Check there are not more than 1 miner associated with the ip
        ip_occurences = get_miner_ip_occurences(axon.ip, ips)

        statistics = await get_hotkey_statistics(axon.hotkey, self.database)
        if statistics is None:
            miner = Miner(
                uid=uid,
                ip=axon.ip,
                hotkey=axon.hotkey,
                country=get_country(axon.ip),
                ip_occurences=ip_occurences,
            )
            await update_hotkey_statistics(axon.hotkey, miner.snapshot, self.database)
        else:
            # In hash set everything is stored as a string to the verified need to be manage differently
            version = get_field_value(statistics.get(b"version"), "0.0.0")
            country = get_field_value(statistics.get(b"country")) or get_country(
                axon.ip
            )
            verified = get_field_value(statistics.get(b"verified"), "0")
            score = get_field_value(statistics.get(b"score"), 0)
            availability_score = get_field_value(
                statistics.get(b"availability_score"), 0
            )
            latency_score = get_field_value(statistics.get(b"latency_score"), 0)
            reliability_score = get_field_value(statistics.get(b"reliability_score"), 0)
            distribution_score = get_field_value(
                statistics.get(b"distribution_score"), 0
            )
            challenge_successes = get_field_value(
                statistics.get(b"challenge_successes"), 0
            )
            challenge_attempts = get_field_value(
                statistics.get(b"challenge_attempts"), 0
            )
            process_time = get_field_value(statistics.get(b"process_time"), 0)

            miner = Miner(
                uid=uid,
                ip=axon.ip,
                ip_occurences=ip_occurences,
                hotkey=axon.hotkey,
                version=version,
                country=country,
                verified=verified == "1",
                score=score,
                availability_score=availability_score,
                latency_score=latency_score,
                reliability_score=reliability_score,
                distribution_score=distribution_score,
                challenge_successes=challenge_successes,
                challenge_attempts=challenge_attempts,
                process_time=process_time,
            )

        miners.append(miner)

    return miners


async def add_new_miner(self, uid: int, ip: str, hotkey: str):
    """
    Add a new miner
    """
    miner = Miner(uid=uid, ip=ip, hotkey=hotkey, country=get_country(ip))
    self.miners.append(miner)

    return miner


async def replace_old_miner(self, ip: str, hotkey: str, miner: Miner):
    """
    Replace the old miner by the new one
    """
    old_hotkey = miner.hotkey

    # Remove the old hotkey statistics
    await remove_hotkey_stastitics(miner.hotkey, self.database)

    # Reset the new miner
    miner.reset(ip, hotkey, get_country(ip))

    return old_hotkey


def move_miner(ip: str, miner: Miner):
    """
    Move an existing miner from a host to another one
    """
    previous_ip = miner.ip

    # Reset the miner as it changed ip so everything has to be re-evaluated
    miner.reset(ip, miner.hotkey, get_country(ip))

    return previous_ip


async def resync_miners(self):
    """
    Resync the miners following a metagraph resynchronisation
    """

    # Focus on the changes in the metagraph
    bt.logging.info("resync_miners() processing metagraph changes")
    uids = get_available_uids(self)
    for uid in uids:
        # Get details
        axon = self.metagraph.axons[uid]
        hotkey = self.metagraph.hotkeys[uid]
        ip = axon.ip

        is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        if not is_available:
            miners = [miner for miner in self.miners if miner.uid != uid]
            if len(miners) < len(self.miners):
                bt.logging.success(
                    f"[{miner.uid}] Miner {hotkey} hase been removed from the list."
                )
                self.miners = miners

            continue

        miner: Miner = next((miner for miner in self.miners if miner.uid == uid), None)

        # Check a new miner registered to the subnet
        if miner is None:
            miner = await add_new_miner(self, uid, ip, hotkey)
            bt.logging.success(f"[{miner.uid}] New miner {hotkey} added to the list.")

        # Check a new miner is replacing an old one
        if miner.hotkey != hotkey:
            old_hotkey = await replace_old_miner(self, ip, hotkey, miner)
            bt.logging.success(
                f"[{miner.uid}] Old miner {old_hotkey} has been replaced by the miner {hotkey}."
            )

        # Check the miner has been moved to another VPS
        if miner.ip != ip:
            previous_ip = move_miner(ip, miner)
            bt.logging.success(
                f"[{miner.uid}] Miner moved from {previous_ip} to {miner.ip}"
            )

    # Focus on impacts resulting of these changes
    bt.logging.debug("resync_miners() refreshing ip occurences")
    ips = [miner.ip for miner in self.miners]
    for miner in self.miners:
        # Refresh the miners ip occurrences
        miner.ip_occurences = get_miner_ip_occurences(miner.ip, ips)

    bt.logging.debug("resync_miners() refreshing scores")
    for miner in self.miners:
        # Refresh the availability score
        miner.availability_score = compute_availability_score(miner)

        # Refresh latency score
        miner.latency_score = compute_latency_score(self.country, miner, self.miners)

        # Refresh the distribution score
        miner.distribution_score = compute_distribution_score(miner, self.miners)

        # Refresh the final score
        miner.score = compute_final_score(miner)

        # Update the miner in the database
        await update_hotkey_statistics(miner.hotkey, miner.snapshot, self.database)


async def reset_reliability_score(self, miners: List[Miner]):
    bt.logging.info("reset_reliability_score() reset reliability statistics.")

    for miner in miners:
        miner.challenge_attempts = 0
        miner.challenge_successes = 0

        await update_hotkey_statistics(miner.hotkey, miner.snapshot, self.database)
