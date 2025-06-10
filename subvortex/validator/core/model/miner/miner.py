import copy
from typing import Dict, Any, List
from dataclasses import dataclass, field

from bittensor.core.axon import AxonInfo


@dataclass
class Miner:
    uid: int = -1
    rank: int = -1
    coldkey: str = None
    hotkey: str = None
    ip: str = "0.0.0.0"
    port: int = 0
    version: str = "0.0.0"
    country: str = None

    # Metadata
    availability_attempts: List[int] = field(default_factory=list)
    availability_successes: List[int] = field(default_factory=list)
    reliability_attempts: List[int] = field(default_factory=list)
    reliability_successes: List[int] = field(default_factory=list)
    latency_times: List[float] = field(default_factory=list)
    performance_attempts: List[int] = field(default_factory=list)
    performance_successes: List[int] = field(default_factory=list)
    performance_boost: List[float] = field(default_factory=list)

    # Scores
    score: float = 0
    availability_score: float = 0
    reliability_score: float = 0
    latency_score: float = 0
    distribution_score: float = 0
    performance_score: float = 0
    moving_score: float = 0

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uid": self.uid,
            "rank": self.rank,
            "hotkey": self.hotkey,
            "ip": self.ip,
            "version": self.version,
            "country": self.country,
            "verified": int(self.verified),
            "score": self.score,
            "availability_score": self.availability_score,
            "reliability_score": self.reliability_score,
            "latency_score": self.latency_score,
            "distribution_score": self.distribution_score,
            "performance_score": self.performance_score,
            "moving_score": self.moving_score,
            "availability_attempts": self.availability_attempts,
            "availability_successes": self.availability_successes,
            "reliability_attempts": self.reliability_attempts,
            "reliability_successes": self.reliability_successes,
            "latency_times": self.latency_times,
            "performance_attempts": self.performance_attempts,
            "performance_successes": self.performance_successes,
            "performance_boost": self.performance_boost,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any], hotkey: str) -> "Miner":
        return Miner(
            uid=int(data.get("uid", -1)),
            rank=int(data.get("rank", -1)),
            hotkey=data.get("hotkey", hotkey),
            ip=data.get("ip", "0.0.0.0"),
            version=data.get("version", "0.0.0"),
            country=data.get("country"),
            verified=bool(int(data.get("verified", 0))),
            score=float(data.get("score", 0)),
            availability_score=float(data.get("availability_score", 0)),
            reliability_score=float(data.get("reliability_score", 0)),
            latency_score=float(data.get("latency_score", 0)),
            distribution_score=float(data.get("distribution_score", 0)),
            performance_score=float(data.get("performance_score", 0)),
            moving_score=float(data.get("moving_score", 0)),
            availability_attempts=data.get("availability_attempts", []),
            availability_successes=data.get("availability_successes", []),
            reliability_attempts=data.get("reliability_attempts", []),
            reliability_successes=data.get("reliability_successes", []),
            latency_times=data.get("latency_times", []),
            performance_attempts=data.get("performance_attempts", []),
            performance_successes=data.get("performance_successes", []),
            performance_boost=data.get("performance_boost", []),
        )

    def reset(self, reset_moving_score=False):
        self.rank = -1
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
        self.performance_score = 0
        self.availability_attempts.clear()
        self.availability_successes.clear()
        self.reliability_attempts.clear()
        self.reliability_successes.clear()
        self.latency_times.clear()
        self.performance_attempts.clear()
        self.performance_successes.clear()
        self.performance_boost.clear()

        if reset_moving_score:
            self.moving_score = 0

    def clone(self) -> "Miner":
        return copy.deepcopy(self)