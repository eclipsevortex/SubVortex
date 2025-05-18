from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu
from subvortex.core.metagraph.settings import Settings as MetagraphSettings


@dataclass
class Settings(MetagraphSettings):
    logging_name: str = field(default="Neuron", metadata={"readonly": True})
    """
    Prefix to use when logging
    """

    redis_host: str = "localhost"
    """
    Host of the redis instance
    """

    redis_port: int = 6379
    """
    Port of the redis instance
    """

    redis_index: int = 0
    """
    Index of the redis instance
    """

    redis_password: str = None
    """
    Password of the redis instance
    """

    weights_setting_attempts: int = field(default=5, metadata={"readonly": True})
    """
    Number of attempts to set weights on the chain
    """

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
