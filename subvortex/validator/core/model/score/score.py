from typing import List
from dataclasses import dataclass, fields

@dataclass
class Score:
    uid: int
    hotkey: str
    schedule_id: str
    success: bool
    reason: str | None

    # Metadata
    availability_attempts: List[int]
    availability_successes: List[int]
    reliability_attempts: List[int]
    reliability_successes: List[int]
    latency_times: List[float]
    performance_attempts: List[int]
    performance_successes: List[int]
    performance_boost: List[float]

    # Scores
    availability_score: float
    reliability_score: float
    latency_score: float
    performance_score: float
    distribution_score: float
    final_score: float
    moving_score: float

    def __init__(
        self,
        uid: int,
        hotkey: str,
        schedule_id: str = "",
        availability_attempts: List[int] = [],
        availability_successes: List[int] = [],
        reliability_attempts: List[int] = [],
        reliability_successes: List[int] = [],
        latency_times: List[float] = [],
        performance_attempts: List[int] = [],
        performance_successes: List[int] = [],
        performance_boost: List[float] = [],
        availability_score: float = 0.0,
        reliability_score: float = 0.0,
        latency_score: float = 0.0,
        distribution_score: float = 0.0,
        performance_score: float = 0.0,
        final_score: float = 0.0,
        moving_score: float = 0.0,
        success: bool = False,
        reason: str | None = None,
    ):
        self.uid = uid
        self.hotkey = hotkey
        self.schedule_id = schedule_id
        self.availability_attempts = availability_attempts
        self.availability_successes = availability_successes
        self.reliability_attempts = reliability_attempts
        self.reliability_successes = reliability_successes
        self.latency_times = latency_times
        self.performance_attempts = performance_attempts
        self.performance_successes = performance_successes
        self.performance_boost = performance_boost
        self.availability_score = availability_score
        self.reliability_score = reliability_score
        self.latency_score = latency_score
        self.distribution_score = distribution_score
        self.performance_score = performance_score
        self.final_score = final_score
        self.moving_score = moving_score
        self.success = success
        self.reason = reason

    @staticmethod
    def convert_to(mapping):
        """Converts a dictionary to a Score instance."""
        return Score(
            uid=int(mapping["uid"]),
            hotkey=mapping["hotkey"],
            schedule_id=mapping["schedule_id"],
            availability_attempts=(
                list(map(int, mapping.get("availability_attempts", "").split(",")))
                if mapping.get("availability_attempts")
                else []
            ),
            availability_successes=(
                list(map(int, mapping.get("availability_successes", "").split(",")))
                if mapping.get("availability_successes")
                else []
            ),
            reliability_attempts=(
                list(map(int, mapping.get("reliability_attempts", "").split(",")))
                if mapping.get("reliability_attempts")
                else []
            ),
            reliability_successes=(
                list(map(int, mapping.get("reliability_successes", "").split(",")))
                if mapping.get("reliability_successes")
                else []
            ),
            latency_times=(
                list(map(float, mapping.get("latency_times", "").split(",")))
                if mapping.get("latency_times")
                else []
            ),
            performance_attempts=(
                list(map(int, mapping.get("performance_attempts", "").split(",")))
                if mapping.get("performance_attempts")
                else []
            ),
            performance_successes=(
                list(map(int, mapping.get("performance_successes", "").split(",")))
                if mapping.get("performance_successes")
                else []
            ),
            performance_boost=(
                list(map(float, mapping.get("performance_boost", "").split(",")))
                if mapping.get("performance_boost")
                else []
            ),
            availability_score=float(mapping.get("availability_score", 0.0)),
            reliability_score=float(mapping.get("reliability_score", 0.0)),
            latency_score=float(mapping.get("latency_score", 0.0)),
            distribution_score=float(mapping.get("distribution_score", 0.0)),
            performance_score=float(mapping.get("performance_score", 0.0)),
            final_score=float(mapping.get("final_score", 0.0)),
            moving_score=float(mapping.get("moving_score", 0.0)),
            success=bool(mapping.get("success")),
            reason=mapping.get("reason"),
        )

    def convert_from(self):
        """Converts a Score instance to a dictionary"""
        return {
            "uid": self.uid,
            "hotkey": self.hotkey,
            "schedule_id": self.schedule_id,
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
            "final_score": self.final_score,
            "moving_score": self.moving_score,
            "success": int(self.success),
            "reason": self.reason or "",
        }

    def __str__(self):
        """Returns a human-readable string representation of the Score instance."""
        return (
            f"Score(schedule_id={self.schedule_id}, success={self.success}, reason={self.reason}, availability_attempts={self.availability_attempts}, availability_successes={self.availability_successes}, reliability_attempts={self.reliability_attempts}, "
            f"reliability_successes={self.reliability_successes}, latency_times={self.latency_times}, "
            f"performance_attempts={self.performance_attempts}, performance_successes={self.performance_successes}, performance_boost={self.performance_boost},"
            f"availability_score={self.availability_score}, reliability_score={self.reliability_score}, "
            f"latency_score={self.latency_score}, distribution_score={self.distribution_score}, "
            f"performance_score={self.performance_score}, final_score={self.final_score}, moving_score={self.moving_score})"
        )

    def __repr__(self):
        """Returns a more detailed string representation useful for debugging."""
        return (
            f"Score(schedule_id={self.schedule_id}, success={self.success}, reason={self.reason}, availability_attempts={self.availability_attempts}, availability_successes={self.availability_successes}, reliability_attempts={self.reliability_attempts}, "
            f"reliability_successes={self.reliability_successes!r}, latency_times={self.latency_times}, "
            f"performance_attempts={self.performance_attempts!r}, performance_successes={self.performance_successes!r}, performance_boost={self.performance_boost!r}, "
            f"availability_score={self.availability_score!r}, reliability_score={self.reliability_score!r}, "
            f"latency_score={self.latency_score!r}, distribution_score={self.distribution_score!r}, "
            f"performance_score={self.performance_score!r}, final_score={self.final_score!r}, moving_score={self.moving_score!r})"
        )
