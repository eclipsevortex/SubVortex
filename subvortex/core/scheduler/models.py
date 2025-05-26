class Schedule:
    pass

class Settings:
    MAX_CHALLENGE_TIME_PER_MINER: int = 2
    """
    Maximum time to challenge a miner
    """

    @staticmethod
    async def create(identity: dict):
        identity = identity or {}
        # Create the settings
        return Settings()