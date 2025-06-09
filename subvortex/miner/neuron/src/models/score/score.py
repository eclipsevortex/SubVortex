from typing import Dict
from dataclasses import dataclass


@dataclass
class Score:
    rank: int = -1
    block: int = -1
    vuid: int = -1
    moving_score: float = 0.0
    score: float = 0.0
    availability_score: float = 0.0
    reliability_score: float = 0.0
    latency_score: float = 0.0
    distribution_score: float = 0.0
    penalty_factor: float = None

    def to_dict(self) -> Dict[str, str]:
        return {
            "vuid": self.vuid,
            "block": self.block,
            "rank": self.rank,
            "availability_score": self.availability_score,
            "latency_score": self.latency_score,
            "reliability_score": self.reliability_score,
            "distribution_score": self.distribution_score,
            "score": self.score,
            "moving_score": self.moving_score,
            "penalty_factor": self.penalty_factor or -1.0,
        }

    @staticmethod
    def from_dict(data: Dict[str, str]) -> "Score":
        penalty_score = data.get("penalty_factor")
        return Score(
            vuid=int(data.get("vuid", -1)),
            block=int(data.get("block", -1)),
            rank=int(data.get("rank", -1)),
            moving_score=float(data.get("moving_score", 0.0)),
            score=float(data.get("score", 0.0)),
            availability_score=float(data.get("availability_score", 0.0)),
            latency_score=float(data.get("latency_score", 0.0)),
            reliability_score=float(data.get("reliability_score", 0.0)),
            distribution_score=float(data.get("distribution_score", 0.0)),
            penalty_factor=float(penalty_score) if penalty_score != -1.0 else None,
        )
