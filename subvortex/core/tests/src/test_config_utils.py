import argparse
from dataclasses import dataclass

import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

from subvortex.core.core_bittensor.config.config_utils import update_config


@dataclass
class BaseSettings:
    netuid: int = 42


@dataclass
class SubtensorSettings:
    network: str = "finney"
    chain_endpoint: str = "https://subtensor.endpoint"


@dataclass
class ServiceSettings(BaseSettings, SubtensorSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_index: int = 0
    redis_password: str = "secret"


def make_parser():
    parser = argparse.ArgumentParser()
    btcas.AsyncSubtensor.add_args(parser)
    btul.logging.add_args(parser)
    parser.add_argument(
        "--netuid", type=int, help="Subvortex network netuid", default=7
    )
    return parser


def test_update_config_with_default_values():
    settings = ServiceSettings()
    config = btcc.Config(parser=make_parser())

    update_config(settings, config)

    assert config.netuid == 42
    assert config.subtensor.network == "finney"
    assert config.subtensor.chain_endpoint == "https://subtensor.endpoint"


def test_update_config_with_overrided_values():
    settings = ServiceSettings(netuid=1, chain_endpoint="https://custom.subtensor.endpoint")
    config = btcc.Config(make_parser())
    update_config(settings, config)

    assert config.netuid == 1
    assert config.subtensor.network == "finney"
    assert config.subtensor.chain_endpoint == "https://custom.subtensor.endpoint"
