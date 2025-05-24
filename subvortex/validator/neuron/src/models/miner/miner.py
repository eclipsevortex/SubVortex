import copy
from typing import Dict, Any
from dataclasses import dataclass, asdict

from bittensor.core.axon import AxonInfo


@dataclass
class Miner:
    uid: int = -1
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Miner":
        return cls(
            uid=int(data.get("uid", -1)),
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

    def to_redis_mapping(self) -> Dict[str, str]:
        return {
            "uid": self.uid,
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

    @classmethod
    def from_redis_mapping(cls, data: Dict[str, str]) -> "Miner":
        return cls(
            uid=int(data.get("uid", -1)),
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
        self.version = "0.0.0"
        self.verified = False
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
