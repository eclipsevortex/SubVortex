from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu


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

    weights_setting_attempts: int = field(default=5, metadata={"readonly": True})
    """
    Number of attempts to set weights on the chain
    """

    dry_run: bool = False
    """
    If True, simulates the operation without executing it on-chain.
    """

    @property
    def is_test(self):
        return self.netuid == 92

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
