from enum import Enum

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
    primary: bool = False

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
        identified=False,
    ):
        self.uid = int(uid) if uid is not None else -1
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
        self.primary = identified or False

    def reset(self, ip, hotkey, country):
        self.hotkey = hotkey
        self.ip = ip
        self.primary = False
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
        self.primary = False

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
        return f"Miner(uid={self.uid}, hotkey={self.hotkey}, ip={self.ip}, ip_occurences={self.ip_occurences}, version={self.version}, country={self.country}, verified={self.verified}, primary={self.primary}, score={self.score}, availability_score={self.availability_score}, latency_score={self.latency_score}, reliability_score={self.reliability_score}, distribution_score={self.distribution_score}, challenge_attempts={self.challenge_attempts}, challenge_successes={self.challenge_successes}, process_time={self.process_time})"

    def __repr__(self):
        return f"Miner(uid={self.uid}, hotkey={self.hotkey}, ip={self.ip}, ip_occurences={self.ip_occurences}, version={self.version}, country={self.country}, verified={self.verified}, primary={self.primary}, score={self.score}, availability_score={self.availability_score}, latency_score={self.latency_score}, reliability_score={self.reliability_score}, distribution_score={self.distribution_score}, challenge_attempts={self.challenge_attempts}, challenge_successes={self.challenge_successes}, process_time={self.process_time})"
