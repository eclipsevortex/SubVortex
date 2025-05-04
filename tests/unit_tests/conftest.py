# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import os
import pytest
import aioredis
import bittensor.utils.btlogging as btul
from unittest.mock import AsyncMock

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
    btul.logging.off()

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
    btul.logging.off()

    yield miner
