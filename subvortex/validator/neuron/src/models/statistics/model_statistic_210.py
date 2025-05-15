from subvortex.validator.neuron.src.models.statistics import StatisticModel200


class StatisticModel(StatisticModel200):
    """
    Versioned model for storing and retrieving hotkey statistics from Redis.
    This is version 2.1.0 of the model.
    """

    version = "2.1.0"

    def redis_key(self, ss58_address: str) -> str:
        """Generate the Redis key for a given hotkey."""
        return f"sv:stats:{ss58_address}"
