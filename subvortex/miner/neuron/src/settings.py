from dotenv import load_dotenv
from dataclasses import dataclass

import subvortex.core.settings_utils as scsu
from subvortex.core.metagraph.settings import Settings as MetagraphSettings

load_dotenv()


@dataclass
class Settings(MetagraphSettings):
    database_host: str = "localhost"
    """
    Host of the redis instance
    """

    database_port: int = 6379
    """
    Port of the redis instance
    """

    database_index: int = 0
    """
    Index of the redis instance
    """

    database_password: str = None
    """
    Password of the redis instance
    """

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
