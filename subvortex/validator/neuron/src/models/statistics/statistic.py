from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class Statistic:
    uid: int = -1
    country: str = ""
    version: str = ""
    verified: str = "0"
    score: str = "0"
    availability_score: str = "0"
    latency_score: str = "0"
    reliability_score: str = "0"
    distribution_score: str = "0"
    challenge_successes: str = "0"
    challenge_attempts: str = "0"
    process_time: str = "0"

    @classmethod
    def from_dict(cls, data: Dict[str, Any], default_version: str = "") -> "Statistic":
        return cls(
            uid=int(data.get("uid", -1)),
            country=data.get("country", ""),
            version=data.get("version", default_version),
            verified=str(data.get("verified", "0")),
            score=str(data.get("score", 0)),
            availability_score=str(data.get("availability_score", 0)),
            latency_score=str(data.get("latency_score", 0)),
            reliability_score=str(data.get("reliability_score", 0)),
            distribution_score=str(data.get("distribution_score", 0)),
            challenge_successes=str(data.get("challenge_successes", 0)),
            challenge_attempts=str(data.get("challenge_attempts", 0)),
            process_time=str(data.get("process_time", 0)),
        )

    def to_redis_mapping(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_redis_mapping(cls, data: Dict[str, str]) -> "Statistic":
        return cls(**data)