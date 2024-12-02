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

from subnet.constants import DEFAULT_CHUNK_SIZE
from subnet.validator.utils import get_next_uids

from tests.unit_tests.mocks import mock_redis
from tests.unit_tests.utils.utils import generate_random_ip
from tests.unit_tests.utils.utils import count_non_unique, count_unique


@pytest.mark.asyncio
@pytest.mark.usefixtures("validator")
async def test_select_uids_fairly(
    validator,
):
    # Step 1
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    val_hotkey = validator.metagraph.hotkeys[validator.uid]
    validator.database = mock_redis.mock_get_selection(val_hotkey)

    # Act
    selection_1 = await get_next_uids(validator, val_hotkey, k=DEFAULT_CHUNK_SIZE)

    # Assert
    assert DEFAULT_CHUNK_SIZE == len(selection_1)
    assert DEFAULT_CHUNK_SIZE == count_unique(selection_1)

    # Step 2
    # Arrange
    val_hotkey = validator.metagraph.hotkeys[validator.uid]
    validator.database = mock_redis.mock_get_selection(val_hotkey, selection_1)

    # Act
    selection_2 = await get_next_uids(validator, val_hotkey, k=DEFAULT_CHUNK_SIZE)

    # Assert
    assert DEFAULT_CHUNK_SIZE == len(selection_2)
    assert DEFAULT_CHUNK_SIZE == count_unique(selection_2)
    assert 3 == count_non_unique(selection_1 + selection_2)
