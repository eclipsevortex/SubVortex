import pytest
import aioredis
from unittest.mock import AsyncMock
import bittensor as bt

from neurons.validator import Validator


@pytest.fixture(scope="session", autouse=True)
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
