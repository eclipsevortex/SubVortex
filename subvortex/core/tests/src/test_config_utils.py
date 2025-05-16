import os
import argparse
from dataclasses import dataclass, field

import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.settings_utils as scsu
from subvortex.core.core_bittensor.config.config_utils import update_config


@dataclass
class EmptySettings:
    """Empty settings for fallback testing."""

    @classmethod
    def create(cls) -> "EmptySettings":
        return cls()


@dataclass
class BaseSettings:
    netuid: int = 7
    logging_name: str = field(default="Name", metadata={"readonly": True})

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)


@dataclass
class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_index: int = 0
    redis_password: str = "secret"

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)


def create_config():
    parser = argparse.ArgumentParser()
    btcas.AsyncSubtensor.add_args(parser)
    btul.logging.add_args(parser)
    return btcc.Config(parser), parser


def test_update_config_with_default_values():
    # Create parser and config
    config, parser = create_config()

    settings = Settings.create()
    update_config(settings, config, parser)

    assert settings.netuid == 7
    assert settings.redis_host == "localhost"
    assert settings.redis_port == 6379
    assert settings.redis_index == 0
    assert settings.redis_password == "secret"


def test_custom_settings():
    # Set environment variables
    os.environ["SUBVORTEX_NETUID"] = "92"
    os.environ["SUBVORTEX_REDIS_HOST"] = "192.168.10.1"
    os.environ["SUBVORTEX_REDIS_PORT"] = "6380"
    os.environ["SUBVORTEX_REDIS_INDEX"] = "14"
    os.environ["SUBVORTEX_REDIS_PASSWORD"] = "mypassword"

    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    assert settings.netuid == 92
    assert settings.redis_host == "192.168.10.1"
    assert settings.redis_port == 6380
    assert settings.redis_index == 14
    assert settings.redis_password == "mypassword"


def test_readonly_settings():
    # Set environment variables
    os.environ["SUBVORTEX_LOGGING_NAME"] = "custom logging"

    # Create parser and config
    config, parser = create_config()

    # Create settings and update config from env
    settings = Settings.create()
    update_config(settings, config, parser)

    # Assert config reflects env vars
    assert settings.logging_name == "Name"


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
    assert "redis_host" not in config_dict
    assert "redis_port" not in config_dict
    assert "redis_index" not in config_dict
    assert "redis_password" not in config_dict


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
