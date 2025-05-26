import os
import argparse
from dataclasses import dataclass

import bittensor.utils.btlogging as btul

from bittensor.core.config import Config
from bittensor.core.subtensor import Subtensor
from subvortex.core.core_bittensor.config.config_utils import update_config

from subvortex.validator.metagraph.src.settings import Settings


@dataclass
class EmptySettings:
    """Empty settings for fallback testing."""

    @classmethod
    def create(cls) -> "EmptySettings":
        return cls()


def create_config():
    parser = argparse.ArgumentParser()
    Subtensor.add_args(parser)
    btul.logging.add_args(parser)
    return Config(parser), parser


def test_default_config():
    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    assert settings.logging_name == "Metagraph"
    assert settings.key_prefix == "sv"
    assert settings.netuid == 7
    assert settings.database_host == "localhost"
    assert settings.database_port == 6379
    assert settings.database_index == 0
    assert settings.database_password is None


def test_custom_settings():
    # Set environment variables
    os.environ["SUBVORTEX_NETUID"] = "92"
    os.environ["SUBVORTEX_DATABASE_HOST"] = "192.168.10.1"
    os.environ["SUBVORTEX_DATABASE_PORT"] = "6380"
    os.environ["SUBVORTEX_DATABASE_INDEX"] = "14"
    os.environ["SUBVORTEX_DATABASE_PASSWORD"] = "mypassword"

    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    assert settings.netuid == 92
    assert settings.database_host == "192.168.10.1"
    assert settings.database_port == 6380
    assert settings.database_index == 14
    assert settings.database_password == "mypassword"


def test_readonly_settings():
    # Set environment variables
    os.environ["SUBVORTEX_LOGGING_NAME"] = "custom logging"
    os.environ["SUBVORTEX_KEY_PREFIX"] = "key_prefix"

    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    assert settings.logging_name == "Metagraph"
    assert settings.key_prefix == "sv"


def test_settings_are_not_included_in_config():
    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    config_dict = config.to_dict()
    assert "logging_name" not in config_dict
    assert "key_prefix" not in config_dict
    assert "netuid" not in config_dict
    assert "database_host" not in config_dict
    assert "database_port" not in config_dict
    assert "database_index" not in config_dict
    assert "database_password" not in config_dict


def test_custom_config():
    # Set environment variables
    os.environ["SUBVORTEX_SUBTENSOR_NETWORK"] = "custom"
    os.environ["SUBVORTEX_SUBTENSOR_CHAIN_ENDPOINT"] = "127.12.13.14:9944"
    os.environ["SUBVORTEX_LOGGING_INFO"] = "True"
    os.environ["SUBVORTEX_LOGGING_DEBUG"] = "True"
    os.environ["SUBVORTEX_LOGGING_TRACE"] = "True"
    os.environ["SUBVORTEX_LOGGING_RECORD_LOG"] = "True"

    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    assert config.subtensor.network == "custom"
    assert config.subtensor.chain_endpoint == "127.12.13.14:9944"
    assert config.logging.info == True
    assert config.logging.debug == True
    assert config.logging.trace == True
    assert config.logging.record_log == True


def test_no_settings_config():
    # Set environment variables
    os.environ["SUBVORTEX_SUBTENSOR_NETWORK"] = "custom"
    os.environ["SUBVORTEX_SUBTENSOR_CHAIN_ENDPOINT"] = "127.12.13.14:9944"
    os.environ["SUBVORTEX_LOGGING_INFO"] = "True"
    os.environ["SUBVORTEX_LOGGING_DEBUG"] = "True"
    os.environ["SUBVORTEX_LOGGING_TRACE"] = "True"
    os.environ["SUBVORTEX_LOGGING_RECORD_LOG"] = "True"

    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = EmptySettings()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    assert config.subtensor.network == "custom"
    assert config.subtensor.chain_endpoint == "127.12.13.14:9944"
    assert config.logging.info == True
    assert config.logging.debug == True
    assert config.logging.trace == True
    assert config.logging.record_log == True
