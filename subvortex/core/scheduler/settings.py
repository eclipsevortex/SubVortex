from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu


@dataclass
class Settings:
    max_challenge_time_per_miner: int = 2
    """
    Maximum time to challenge a miner
    """

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
