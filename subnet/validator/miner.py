import bittensor as bt
from typing import List

from subnet.validator.utils import get_available_uids, check_uid_availability
from subnet.validator.localisation import get_country
from subnet.validator.database import (
    get_hotkey_statistics,
    remove_hotkey_stastitics,
    get_field_value,
)


class Miner:
    uid: int = -1
    hotkey: str = None
    ip: str = ("0.0.0.0",)
    ip_occurences: int = 1
    version: str = "0.0.0"
    country: str = None
    score: float = 0
    availability_score: float = 0
    reliability_score: float = 0
    latency_score: float = 0
    distribution_score: float = 0
    challenge_successes: int = 0
    challenge_attempts: int = 0
    process_time: float = 0
    verified: bool = False

    def __init__(
        self,
        uid,
        ip,
        hotkey,
        country,
        version="0.0.0",
        verified=False,
        score=0,
        availability_score=0,
        latency_score=0,
        reliability_score=0,
        distribution_score=0,
        challenge_successes=0,
        challenge_attempts=0,
        process_time=0,
        ip_occurences=1,
    ):
        self.uid = int(uid or -1)
        self.hotkey = hotkey
        self.ip = ip or "0.0.0.0"
        self.ip_occurences = ip_occurences
        self.version = version or "0.0.0"
        self.country = country or ""
        self.verified = verified or False
        self.score = float(score or 0)
        self.availability_score = float(availability_score or 0)
        self.reliability_score = float(reliability_score or 0)
        self.latency_score = float(latency_score or 0)
        self.distribution_score = float(distribution_score or 0)
        self.challenge_successes = int(challenge_successes or 0)
        self.challenge_attempts = int(challenge_attempts or 0)
        self.process_time = float(process_time or 0)

    def reset(self, ip, hotkey, country):
        self.hotkey = hotkey
        self.ip = ip
        self.version = "0.0.0"
        self.country = country or ""
        self.verified = False
        self.score = 0
        self.availability_score = 0
        self.reliability_score = 0
        self.latency_score = 0
        self.distribution_score = 0
        self.challenge_successes = 0
        self.challenge_attempts = 0
        self.process_time = 0

    @property
    def has_ip_conflicts(self):
        return self.ip_occurences != 1

    @property
    def snapshot(self):
        # index and ip are not stored in redis database
        # index because we do not need
        # ip/hotkey because we do not to keep a track of them
        return {
            "uid": self.uid,
            "version": self.version,
            "country": self.country,
            "verified": int(self.verified),
            "score": self.score,
            "availability_score": self.availability_score,
            "latency_score": self.latency_score,
            "reliability_score": self.reliability_score,
            "distribution_score": self.distribution_score,
            "challenge_successes": self.challenge_successes,
            "challenge_attempts": self.challenge_attempts,
            "process_time": self.process_time,
        }

    def __str__(self):
        return f"Miner(uid={self.uid}, hotkey={self.hotkey}, ip={self.ip}, ip_occurences={self.ip_occurences}, version={self.version}, country={self.country}, verified={self.verified}, score={self.score}, availability_score={self.availability_score}, latency_score={self.latency_score}, reliability_score={self.reliability_score}, distribution_score={self.distribution_score}, challenge_attempts={self.challenge_attempts}, challenge_successes={self.challenge_successes}, process_time={self.process_time})"

    def __repr__(self):
        return f"Miner(uid={self.uid}, hotkey={self.hotkey}, ip={self.ip}, ip_occurences={self.ip_occurences}, version={self.version}, country={self.country}, verified={self.verified}, score={self.score}, availability_score={self.availability_score}, latency_score={self.latency_score}, reliability_score={self.reliability_score}, distribution_score={self.distribution_score}, challenge_attempts={self.challenge_attempts}, challenge_successes={self.challenge_successes}, process_time={self.process_time})"


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

    # Update the new hotkey statistics
    miner.reset(ip, hotkey, get_country(ip))

    return old_hotkey


def move_miner(ip: str, miner: Miner):
    """
    Add a new miner
    """
    previous_ip = miner.ip

    miner.ip = ip
    miner.country = get_country(ip)

    return previous_ip


async def resync_miners(self):
    """
    Resync the miners following a metagraph resynchronisation
    """
    bt.logging.info("resync_miners()")

    for uid, axon in enumerate(self.metagraph.axons):
        # Get details
        ip = axon.ip
        hotkey = self.metagraph.hotkeys[uid]

        is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        if not is_available:
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

        # Refresh the miners ip occurrences of the impacted miners
        ips = [miner.ip for miner in self.miners]
        for item in self.miners:
            item.ip_occurences = get_miner_ip_occurences(item.ip, ips)

            
