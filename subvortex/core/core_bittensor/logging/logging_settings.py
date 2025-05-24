from dotenv import load_dotenv
from dataclasses import dataclass

import subvortex.core.settings_utils as scsu

load_dotenv()


@dataclass
class Settings:
    info: bool = True
    """
    Turn on bittensor info level information
    """

    debug: bool = True
    """
    Turn on bittensor debugging information
    """

    trace: bool = False
    """
    Turn on bittensor trace level information
    """

    record_log: bool = False
    """
    Turns on logging to file.
    """

    @staticmethod
    def create() -> "Settings":
        return scsu.create_settings_instance(Settings)

