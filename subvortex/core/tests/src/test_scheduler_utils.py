import pytest
import math
from types import SimpleNamespace
from subvortex.core.scheduler.utils import get_step_blocks

# Mock constants
import subvortex.core.scheduler.constants as scsc

@pytest.fixture(autouse=True)
def patch_block_build_time(monkeypatch):
    # Patch BLOCK_BUILD_TIME to a known constant
    monkeypatch.setattr(scsc, "BLOCK_BUILD_TIME", 5.0)  # seconds
    yield


@pytest.mark.parametrize("counter, max_time, expected_blocks", [
    # max_occurence = 3, total_time = 3 * 10 = 30, blocks = ceil(30/5) + 1 = 7
    ({"us": 1, "de": 3, "fr": 2}, 10.0, 7),

    # max_occurence = 5, total_time = 5 * 12 = 60, blocks = ceil(60/5) + 1 = 13
    ({"a": 5}, 12.0, 13),

    # max_occurence = 1, total_time = 1 * 5 = 5, blocks = ceil(5/5) + 1 = 2
    ({"only": 1}, 5.0, 2),

    # max_occurence = 4, total_time = 4 * 1 = 4, blocks = ceil(4/5) + 1 = 2
    ({"a": 4, "b": 1}, 1.0, 2),
])
def test_get_step_blocks(counter, max_time, expected_blocks):
    settings = SimpleNamespace(max_challenge_time_per_miner=max_time)
    result = get_step_blocks(settings, counter)
    assert result == expected_blocks


def test_get_step_blocks_empty_counter():
    settings = SimpleNamespace(max_challenge_time_per_miner=10.0)
    counter = {}
    assert get_step_blocks(settings, counter) == 0
