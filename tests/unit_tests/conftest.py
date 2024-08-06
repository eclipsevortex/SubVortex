import pytest
import aioredis
from unittest.mock import AsyncMock
import bittensor as bt

from neurons.validator import Validator
from neurons.miner import Miner


@pytest.fixture(scope="session", autouse=False)
def validator():
    config = Validator.config()
    config.mock = True
    config.wandb.off = True
    config.neuron.dont_save_events = True
    validator = Validator(config)
    validator.country_code = "GB"
    bt.logging.off()

    mock = AsyncMock(aioredis.Redis)
    mock_instance = mock.return_value
    validator.database = mock_instance

    yield validator


@pytest.fixture(scope="session", autouse=False)
def miner():
    config = Miner.config()
    config.mock = True
    config.wallet._mock = True
    config.miner.mock_subtensor = True
    config.netuid = 1
    miner = Miner(config)
    bt.logging.off()

    yield miner
