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
from typing import List
from unittest.mock import AsyncMock


def mock_get_selection(hoktkey: str, selection: List[int] = None):
    # Mock the redis instance
    mocked_redis = AsyncMock()

    # Set the return value for redis.get
    selection_key = f"selection:{hoktkey}"
    selection_value = ", ".join(map(str, selection)).encode() if selection else None
    mocked_redis.get = AsyncMock(
        side_effect=lambda key: (selection_value if key == selection_key else None)
    )

    return mocked_redis


def mock_get_statistics(hoktkeys: List[str]):
    # Mock the redis instance
    mocked_redis = AsyncMock()

    # Set the return value for redis.get
    selection_keys = [f"stats:{hotkey}" for hotkey in hoktkeys]
    mocked_redis.hgetall = AsyncMock(
        side_effect=lambda key: (None if key in selection_keys else None)
    )

    return mocked_redis


def rollout_side_effect(*args, **kwargs):
    if rollout_side_effect.called:
        # Do nothing on subsequent calls
        return True
    else:
        # Raise an error on the first call
        rollout_side_effect.called = True
        raise ValueError("Simulated error")
