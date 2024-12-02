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
import bittensor.utils.btlogging as btul
from typing import List

from subnet.validator.models import Miner
from subnet.validator.score import (
    compute_distribution_score,
    compute_availability_score,
    compute_latency_score,
    compute_final_score,
)
from subnet.validator.utils import get_available_uids, check_uid_availability
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

    # Get all the ipds from the miners

    btul.logging.debug("get_all_miners() load miners")
    uids = get_available_uids(self)

    # Get all the ips from available miners
    ips = [self.metagraph.axons[uid].ip for uid in uids]

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
                country=self.country_service.get_country(axon.ip),
                ip_occurences=ip_occurences,
            )
        else:
            # In hash set everything is stored as a string to the verified need to be manage differently
            country = self.country_service.get_country(axon.ip)
            if country == None:
                country = get_field_value(statistics.get(b"country"))

            version = get_field_value(statistics.get(b"version"), "0.0.0")
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

        # Update the database just to be sure we have the right country
        await update_hotkey_statistics(axon.hotkey, miner.snapshot, self.database)

        miners.append(miner)

    return miners


async def add_new_miner(self, uid: int, ip: str, hotkey: str):
    """
    Add a new miner
    """
    miner = Miner(
        uid=uid, ip=ip, hotkey=hotkey, country=self.country_service.get_country(ip)
    )
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
    miner.reset(ip, hotkey, self.country_service.get_country(ip))

    return old_hotkey


def move_miner(self, ip: str, miner: Miner):
    """
    Move an existing miner from a host to another one
    """
    previous_ip = miner.ip

    # Reset the miner as it changed ip so everything has to be re-evaluated
    miner.reset(ip, miner.hotkey, self.country_service.get_country(ip))

    return previous_ip


async def remove_miner(self, uid: int, hotkey: str):
    """
    Remove a miner that is not available anymore
    """
    miners = [miner for miner in self.miners if miner.uid != uid]
    if len(miners) >= len(self.miners):
        return False

    # Remove the statistics
    await remove_hotkey_stastitics(hotkey, self.database)

    # Remove the miner
    self.miners = miners

    return True


async def resync_miners(self):
    """
    Resync the miners following a metagraph resynchronisation
    """

    # Focus on the changes in the metagraph
    btul.logging.info("resync_miners() processing metagraph changes")
    for uid, axon in enumerate(self.metagraph.axons):
        # Get details
        hotkey = self.metagraph.hotkeys[uid]
        ip = axon.ip

        # Check the miner is unavailable
        is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        if not is_available:
            removed = await remove_miner(self, uid, hotkey)
            if removed:
                btul.logging.success(
                    f"[{uid}] Miner {hotkey} has been removed from the list"
                )
            continue

        miner: Miner = next((miner for miner in self.miners if miner.uid == uid), None)

        # Check a new miner registered to the subnet
        if miner is None:
            miner = await add_new_miner(self, uid, ip, hotkey)
            btul.logging.success(f"[{miner.uid}] New miner {hotkey} added to the list")

        # Check a new miner is replacing an old one
        if miner.hotkey != hotkey:
            old_hotkey = await replace_old_miner(self, ip, hotkey, miner)
            btul.logging.success(
                f"[{miner.uid}] Old miner {old_hotkey} has been replaced by the miner {hotkey}"
            )

        # Check the miner has been moved to another VPS
        if miner.ip != ip:
            previous_ip = move_miner(self, ip, miner)
            btul.logging.success(
                f"[{miner.uid}] Miner moved from {previous_ip} to {miner.ip}"
            )

        # Check if the country has been overrided
        country_overrided = self.country_service.get_country(miner.ip)
        if country_overrided and miner.country != country_overrided:
            previous_country = miner.country
            miner.country = country_overrided
            btul.logging.success(
                f"[{miner.uid}][{previous_country}] Miner's country overrided by {miner.country}"
            )

    # Focus on impacts resulting of these changes
    btul.logging.debug("resync_miners() refreshing ip occurences")
    ips = [miner.ip for miner in self.miners]
    for miner in self.miners:
        # Refresh the miners ip occurrences
        miner.ip_occurences = get_miner_ip_occurences(miner.ip, ips)

    btul.logging.debug("resync_miners() refreshing scores")
    locations = self.country_service.get_locations()
    for miner in self.miners:
        # Refresh the availability score
        miner.availability_score = compute_availability_score(miner)

        # Refresh latency score
        miner.latency_score = compute_latency_score(
            self.country_code, miner, self.miners, locations
        )

        # Refresh the distribution score
        miner.distribution_score = compute_distribution_score(miner, self.miners)

        # Refresh the final score
        miner.score = compute_final_score(miner)

        # Update the miner in the database
        await update_hotkey_statistics(miner.hotkey, miner.snapshot, self.database)


async def reset_reliability_score(self, miners: List[Miner]):
    btul.logging.info("reset_reliability_score() reset reliability statistics.")

    for miner in miners:
        miner.challenge_attempts = 0
        miner.challenge_successes = 0

        await update_hotkey_statistics(miner.hotkey, miner.snapshot, self.database)
