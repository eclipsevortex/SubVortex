from dotenv import load_dotenv
from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu

load_dotenv()


@dataclass
class Settings:
    logging_name: str = field(default="Metagraph", metadata={"readonly": True})
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

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
