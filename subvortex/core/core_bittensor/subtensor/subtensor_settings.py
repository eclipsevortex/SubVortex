import os
from dotenv import load_dotenv
from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu

load_dotenv()


@dataclass
class Settings:
    logging_name: str = field(default="Subtensor", metadata={"readonly": True})
    """
    Prefix to use when logging
    """

    network: str = "finney"
    """
    The subtensor network flag. The likely choices are:
        -- finney (main network)
        -- test (test network)
        -- archive (archive network +300 blocks)
        -- local (local running network)
    If this option is set it overloads subtensor.chain_endpoint with
    an entry point node from that network.
    """

    chain_endpoint: str = None
    """
    The subtensor endpoint flag. If set, overrides the --network flag.
    """

    @staticmethod
    def create() -> "Settings":
        return scsu.create_settings_instance(Settings)

