import os
import argparse
from dataclasses import dataclass

import bittensor_wallet.wallet as btw
import bittensor.core.subtensor as btcs
import bittensor.core.axon as btca
import bittensor.utils.btlogging as btul

from bittensor.core.config import Config
from bittensor.core.subtensor import Subtensor
from subvortex.core.core_bittensor.config.config_utils import update_config

from subvortex.miner.neuron.src.settings import Settings


@dataclass
class EmptySettings:
    """Empty settings for fallback testing."""

    @classmethod
    def create(cls) -> "EmptySettings":
        return cls()


def create_config():
    parser = argparse.ArgumentParser()
    btcs.Subtensor.add_args(parser)
    btul.logging.add_args(parser)
    btw.Wallet.add_args(parser)
    btca.Axon.add_args(parser)
    return Config(parser)


def test_default_config():
    # Create parser and config
    config = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config)

    # Assert config reflects env vars
    assert config.netuid == 7
    assert config.redis_host == "localhost"
    assert config.redis_port == 6379
    assert config.redis_index == 0
    assert config.redis_password is None


def test_config():
    # Set environment variables
    os.environ["SUBVORTEX_NETUID"] = "92"
    os.environ["SUBVORTEX_REDIS_HOST"] = "127.12.13.15"
    os.environ["SUBVORTEX_REDIS_PORT"] = "6333"
    os.environ["SUBVORTEX_REDIS_INDEX"] = "13"
    os.environ["SUBVORTEX_REDIS_PASSWORD"] = "mypassword"

    # Create parser and config
    config = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config)

    # Assert config reflects env vars
    assert config.netuid == 92
    assert config.redis_host == "127.12.13.15"
    assert config.redis_port == 6333
    assert config.redis_index == 13
    assert config.redis_password == "mypassword"


def test_readonly_config():
    # Set environment variables
    os.environ["SUBVORTEX_LOGGING_NAME"] = "custom logging"
    os.environ["SUBVORTEX_KEY_PREFIX"] = "key_prefix"

    # Create parser and config
    config = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config)

    # Assert config reflects env vars
    assert config.logging_name == "Metagraph"
    assert config.key_prefix == "sv"


def test_no_settings_config():
    # Set environment variables
    os.environ["SUBVORTEX_WALLET_NAME"] = "wallet name"
    os.environ["SUBVORTEX_WALLET_HOTKEY"] = "hotkey"
    os.environ["SUBVORTEX_AXON_IP"] = "192.168.10.1"
    os.environ["SUBVORTEX_AXON_PORT"] = "1234"
    os.environ["SUBVORTEX_SUBTENSOR_NETWORK"] = "custom"
    os.environ["SUBVORTEX_SUBTENSOR_CHAIN_ENDPOINT"] = "127.12.13.14:9944"
    os.environ["SUBVORTEX_NETUID"] = "92"
    os.environ["SUBVORTEX_REDIS_HOST"] = "127.12.13.15"
    os.environ["SUBVORTEX_REDIS_PORT"] = "6333"
    os.environ["SUBVORTEX_REDIS_INDEX"] = "13"
    os.environ["SUBVORTEX_REDIS_PASSWORD"] = "mypassword"
    os.environ["SUBVORTEX_LOGGING_INFO"] = "True"
    os.environ["SUBVORTEX_LOGGING_DEBUG"] = "True"
    os.environ["SUBVORTEX_LOGGING_TRACE"] = "True"
    os.environ["SUBVORTEX_LOGGING_RECORD_LOG"] = "True"

    # Create parser and config
    config = create_config()

    # Create settings and update config from env
    settings = EmptySettings()
    update_config(settings, config)

    # Assert config reflects env vars
    assert config.wallet.name == "wallet name"
    assert config.wallet.hotkey == "hotkey"
    assert config.axon.ip == "192.168.10.1"
    assert config.axon.port == 1234
    assert config.subtensor.network == "custom"
    assert config.subtensor.chain_endpoint == "127.12.13.14:9944"
    assert config.logging.info == True
    assert config.logging.debug == True
    assert config.logging.trace == True
    assert config.logging.record_log == True
