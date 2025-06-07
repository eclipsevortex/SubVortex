from dotenv import load_dotenv
from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu

load_dotenv()


@dataclass
class Settings:
    logging_name: str = field(default="Neuron", metadata={"readonly": True})
    """
    Prefix to use when logging
    """

    key_prefix: str = field(default="sv", metadata={"readonly": True})
    """
    Prefix to use for each key of the storage
    """

    netuid: int = 7
    """
    UID of the subnet
    """

    metagraph_sync_interval: int = 100
    """
    Interval the metagraph is forced to resync
    """

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
