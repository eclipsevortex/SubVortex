from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu


@dataclass
class Settings:
    logging_name: str = field(default="Challenger", metadata={"readonly": True})
    """
    Prefix to use when logging
    """
    
    netuid: int = 7
    """
    UID of the subnet
    """
    
    default_challenge_max_iteration = 1  # TODO: Resotre 64 when going to prod
    """
    Number of connection that can be opened to a node at the same time.
    """

    challenge_timeout: int = 5
    """
    Duration in second of the challenge
    """

    max_challenge_time_per_miner: int = 2
    """
    Maximum time to challenge a miner
    """

    challenge_period: int = 50
    """
    Period to take into account to compute the sma score
    """

    moving_score_alpha: float = 0.5
    """
    Factor controlling the weight of recent score in a moving average calculation.
    """

    availability_weight: int = 8
    """
    Weight to use for the availability score in the conputation of the final score
    """

    reliability_weight: int = 3
    """
    Weight to use for the reliability score in the conputation of the final score
    """

    latency_weight: int = 7
    """
    Weight to use for the latency score in the conputation of the final score
    """

    performance_weight: int = 7
    """
    Weight to use for the performance score in the conputation of the final score
    """

    distribution_weight: int = 2
    """
    Weight to use for the distribution score in the conputation of the final score
    """

    performance_reward_exponent: float = 0.7
    """
    Controls the non-linear scaling of rewards based on the number of challenge attempts. Higher values amplify rewards for handling more attempts.
    """

    performance_penalty_factor: float = 0.7
    """
    Reduces the score for challengers with a low success ratio, penalizing excessive failed attempts.
    """

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
