import copy
from typing import Dict, Any
from dataclasses import dataclass, asdict

from bittensor.core.axon import AxonInfo


@dataclass
class Miner:
    uid: int = -1
    rank: int = -1
    registered_at: int = 0
    coldkey: str = None
    hotkey: str = None
    ip: str = "0.0.0.0"
    port: int = 0
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
    # True if the miner subtensor is sync which mean the block is equal or more recent than the validator one
    sync: bool = False
    # True if the miner is suspicious (its weight will be 0), false otherwise
    suspicious: bool = False
    penalty_factor: int = None

    # Axon information
    axon_version: str = None
    ip_type: int = 0
    protocol: int = 4
    placeholder1: int = 0
    placeholder2: int = 0

    @property
    def axon(self):
        return AxonInfo.from_dict(
            {
                "coldkey": self.coldkey,
                "hotkey": self.hotkey,
                "ip": self.ip,
                "ip_type": self.ip_type,
                "port": self.port,
                "version": self.axon_version,
                "protocol": self.protocol,
                "placeholder1": self.placeholder1,
                "placeholder2": self.placeholder2,
            }
        )

    @staticmethod
    def create_new_miner(uid: int):
        return Miner(
            uid=uid,
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "uid": self.uid,
            "rank": self.rank,
            "hotkey": self.hotkey,
            "registered_at": self.registered_at,
            "ip": self.ip or "0.0.0.0",
            "country": self.country or "",
            "version": self.version,
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

    @staticmethod
    def from_dict(data: Dict[str, str], hotkey: str) -> "Miner":
        return Miner(
            uid=int(data.get("uid", -1)),
            rank=int(data.get("rank", -1)),
            hotkey=data.get("hotkey", hotkey),
            registered_at=int(data.get("registered_at", 0)),
            ip=data.get("ip", "0.0.0.0"),
            country=data.get("country", None),
            version=data.get("version", "0.0.0"),
            verified=bool(int(data.get("verified", 0))),
            score=float(data.get("score", 0)),
            availability_score=float(data.get("availability_score", 0)),
            latency_score=float(data.get("latency_score", 0)),
            reliability_score=float(data.get("reliability_score", 0)),
            distribution_score=float(data.get("distribution_score", 0)),
            challenge_successes=int(data.get("challenge_successes", 0)),
            challenge_attempts=int(data.get("challenge_attempts", 0)),
            process_time=float(data.get("process_time", 0)),
        )

    def reset(self):
        self.rank = -1
        self.version = "0.0.0"
        self.verified = False
        self.registered_at = 0
        self.sync = False
        self.suspicious = False
        self.penalty_factor = None
        self.score = 0
        self.availability_score = 0
        self.reliability_score = 0
        self.latency_score = 0
        self.distribution_score = 0
        self.challenge_successes = 0
        self.challenge_attempts = 0
        self.process_time = 0

    def clone(self) -> "Miner":
        return copy.deepcopy(self)
