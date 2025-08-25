from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu


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

    sync_interval: int = 100
    """
    Force resync every X blocks to keep neuron data fresh
    """

    dry_run: bool = False
    """
    Run the metagraph in dry mode
    """

    maxmind_license_key: str = None
    """
    MaxMind GeoLite2 license key for automated CSV downloads
    """

    maxmind_output_dir: str = None
    """
    Output directory for MaxMind GeoLite2 CSV files storage
    """

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
