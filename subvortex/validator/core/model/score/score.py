from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class Score:
    uid: int
    hotkey: str
    node_id: str
    success: bool
    reason: str | None

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
    performance_score: float = 0
    distribution_score: float = 0

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Score":
        """Converts a dictionary to a Score instance."""
        return Score(
            uid=int(data["uid"]),
            hotkey=data["hotkey"],
            node_id=int(data["node_id"]),
            availability_attempts=(
                list(map(int, data.get("availability_attempts", "").split(",")))
                if data.get("availability_attempts")
                else []
            ),
            availability_successes=(
                list(map(int, data.get("availability_successes", "").split(",")))
                if data.get("availability_successes")
                else []
            ),
            reliability_attempts=(
                list(map(int, data.get("reliability_attempts", "").split(",")))
                if data.get("reliability_attempts")
                else []
            ),
            reliability_successes=(
                list(map(int, data.get("reliability_successes", "").split(",")))
                if data.get("reliability_successes")
                else []
            ),
            latency_times=(
                list(map(float, data.get("latency_times", "").split(",")))
                if data.get("latency_times")
                else []
            ),
            performance_attempts=(
                list(map(int, data.get("performance_attempts", "").split(",")))
                if data.get("performance_attempts")
                else []
            ),
            performance_successes=(
                list(map(int, data.get("performance_successes", "").split(",")))
                if data.get("performance_successes")
                else []
            ),
            performance_boost=(
                list(map(float, data.get("performance_boost", "").split(",")))
                if data.get("performance_boost")
                else []
            ),
            availability_score=float(data.get("availability_score", 0.0)),
            reliability_score=float(data.get("reliability_score", 0.0)),
            latency_score=float(data.get("latency_score", 0.0)),
            distribution_score=float(data.get("distribution_score", 0.0)),
            performance_score=float(data.get("performance_score", 0.0)),
            score=float(data.get("score", 0.0)),
            success=bool(data.get("success")),
            reason=data.get("reason"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts a Score instance to a dictionary"""
        return {
            "uid": self.uid,
            "hotkey": self.hotkey,
            "node_id": self.node_id,
            "availability_attempts": ",".join(map(str, self.availability_attempts)),
            "availability_successes": ",".join(map(str, self.availability_successes)),
            "reliability_attempts": ",".join(map(str, self.reliability_attempts)),
            "reliability_successes": ",".join(map(str, self.reliability_successes)),
            "latency_times": ",".join(map(str, self.latency_times)),
            "performance_attempts": ",".join(map(str, self.performance_attempts)),
            "performance_successes": ",".join(map(str, self.performance_successes)),
            "performance_boost": ",".join(map(str, self.performance_boost)),
            "availability_score": self.availability_score,
            "reliability_score": self.reliability_score,
            "latency_score": self.latency_score,
            "distribution_score": self.distribution_score,
            "performance_score": self.performance_score,
            "score": self.score,
            "success": int(self.success),
            "reason": self.reason or "",
        }
