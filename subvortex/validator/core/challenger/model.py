from dataclasses import dataclass


@dataclass
class TaskResult:
    # True if the node can answer at least one request, false otherwise
    is_available: bool

    # True if the node's answer correctly, false otherwise
    is_reliable: bool

    # Reason of the failure of the challenge (is_availble and/or is_reliable is false)
    reason: str

    # List of the time took for each request of the challenge
    process_time: float

    @staticmethod
    def create(
        is_available: bool,
        is_reliable: bool,
        reason: str,
        process_time: int,
    ):
        return TaskResult(
            is_available=is_available,
            is_reliable=is_reliable,
            reason=reason,
            process_time=process_time,
        )


@dataclass
class ChallengeResult:
    # Id of the node
    id: str

    # Name of the blockchain of the node
    chain: str

    # Name of the type of the node
    type: str

    # True if the node can answer at least one request, false otherwise
    is_available: bool

    # True if the node's answer correctly, false otherwise
    is_reliable: bool

    # Reason of the failure of the challenge (is_available and/or is_reliable is false)
    reason: str

    # Number of attempts to challenge the node
    challenge_attempts: int

    # Number of success to challenge the node
    challenge_successes: int

    # Average time of all the successful challenge
    avg_process_time: float

    @property
    def is_successful(self):
        """
        True if the node is available and reliable, false otherwise
        """
        return self.is_available and self.is_reliable

    @staticmethod
    def create_default(
        id: str,
        chain: str,
        type: str,
        is_available=False,
        is_reliable=False,
        reason="",
        challenge_attempts=0,
        challenge_successes=0,
        avg_process_time=0,
    ):
        return ChallengeResult(
            id=id,
            chain=chain,
            type=type,
            is_available=is_available,
            is_reliable=is_reliable,
            reason=reason,
            challenge_attempts=challenge_attempts,
            challenge_successes=challenge_successes,
            avg_process_time=avg_process_time,
        )

    @staticmethod
    def create_failed(reason: str, challenge_attempts: int, avg_process_time: float):
        return ChallengeResult(
            chain=None,
            type=None,
            is_available=False,
            is_reliable=False,
            reason=reason,
            challenge_attempts=challenge_attempts,
            challenge_successes=0,
            avg_process_time=avg_process_time,
        )
