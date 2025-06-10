import pytest
from unittest.mock import MagicMock

from subvortex.core.scheduler.scheduler_cycle import (
    get_next_cycle,
    get_epoch_containing_block,
)

import subvortex.core.scheduler.utils as scsu


@pytest.mark.parametrize(
    "block, tempo, adjust, expected_range",
    [
        # block=0, netuid=7, tempo=10, adjust=1
        # interval = 11, last_epoch = 0 - 1 - (0 + 7 + 1) % 11 = -9
        # range(-9, 2)
        (0, 10, 1, range(-9, 2)),
        # block=100, netuid=7, tempo=10, adjust=1
        # interval = 11
        # last_epoch = 100 - 1 - (100 + 7 + 1) % 11 = 99 - 9 = 90
        # range(90, 101)
        (100, 10, 1, range(90, 101)),
        # block=111, netuid=7, tempo=10, adjust=1
        # 119 % 11 = 9 → 111 - 1 - 9 = 101 → range(101, 112)
        (111, 10, 1, range(101, 112)),
        # block=50, netuid=7, tempo=20, adjust=2
        # 59 % 22 = 15 → 50 - 2 - 15 = 33 → range(33, 55)
        (50, 20, 2, range(33, 55)),
    ],
)
def test_get_epoch_containing_block_with_netuid_7(block, tempo, adjust, expected_range):
    netuid = 7
    result = get_epoch_containing_block(block, netuid, tempo, adjust)
    assert result == expected_range


def test_get_epoch_containing_block_asserts_on_zero_tempo():
    with pytest.raises(AssertionError):
        get_epoch_containing_block(block=100, netuid=0, tempo=0, adjust=1)


def test_get_next_cycle_basic(monkeypatch):
    settings = MagicMock()
    counter = {"us": 1, "de": 2, "fr": 3}
    block = 500
    netuid = 0

    # Patch get_step_blocks for this test
    monkeypatch.setattr(scsu, "get_step_blocks", lambda settings, counter: 10)

    expected_tempo = len(counter) * 10
    expected_epoch = get_epoch_containing_block(
        block=block,
        netuid=netuid,
        tempo=expected_tempo,
        adjust=0,
    )

    result = get_next_cycle(settings, netuid, block, counter)
    assert result == expected_epoch


@pytest.mark.parametrize(
    "counter, step_block_value, expected_tempo",
    [
        ({"us": 1}, 10, 10),
        ({"us": 1, "de": 1}, 5, 10),
    ],
)
def test_get_next_cycle_varied_counter(monkeypatch, counter, step_block_value, expected_tempo):
    settings = MagicMock()
    block = 300
    netuid = 0

    monkeypatch.setattr(scsu, "get_step_blocks", lambda settings, counter: step_block_value)

    result = get_next_cycle(settings, netuid, block, counter)
    assert len(result) == expected_tempo
