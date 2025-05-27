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
import pytest
from hashlib import sha256
from typing import Optional

import subvortex.core.core_bittensor.wallet as scbtw
import subvortex.core.shared.mock as scsm


def get_block_hash(block: Optional[int] = None) -> str:
    return "0x" + sha256(str(block).encode()).hexdigest()[:64]


def make_async(method):
    """Wraps a mock's return value in an async function."""

    async def async_wrapper(*args, **kwargs):
        return method(*args, **kwargs)

    return async_wrapper


@pytest.fixture(scope="session", autouse=False)
def subtensor():
    wallet = scbtw.get_mock_wallet()
    subtensor = scsm.MockSubtensor(netuid=1, wallet=wallet)

    # Make some sync method async
    subtensor.get_block_hash = make_async(subtensor.get_block_hash)
    subtensor.substrate.get_block_hash = make_async(get_block_hash)

    yield subtensor
