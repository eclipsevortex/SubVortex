import pytest
import random
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from subvortex.validator.neuron.src.selection import (
    get_available_uids,
    get_pseudorandom_uids,
    get_available_query_miners,
    get_next_uids,
)


class DummyMiner:
    def __init__(self, uid, ip):
        self.uid = uid
        self.ip = ip


def test_get_available_uids_filters_correctly():
    self = SimpleNamespace(
        miners=[
            DummyMiner(uid=0, ip="0.0.0.0"),
            DummyMiner(uid=1, ip="192.168.1.1"),
            DummyMiner(uid=2, ip="192.168.1.2"),
        ]
    )

    result = get_available_uids(self, exclude=[2])
    assert result == [1]


@patch("subvortex.validator.neuron.src.selection.get_block_seed", return_value=42)
async def test_get_pseudorandom_uids_is_deterministic(mock_seed):
    self = SimpleNamespace(subtensor=object())  # just needs to exist
    uids = list(range(10))

    sample1 = get_pseudorandom_uids(self, uids, k=5)
    sample2 = get_pseudorandom_uids(self, uids, k=5)

    assert sample1 == sample2
    assert len(sample1) == 5


@patch("subvortex.validator.neuron.src.selection.get_block_seed", return_value=42)
async def test_get_available_query_miners(mock_seed):
    self = SimpleNamespace(
        miners=[DummyMiner(uid=i, ip="192.168.1.1") for i in range(10)],
        subtensor=object(),
    )

    result = get_available_query_miners(self, k=5, exclude=[0, 1])
    assert len(result) == 5
    assert all(uid not in [0, 1] for uid in result)


@pytest.mark.asyncio
@patch("subvortex.validator.neuron.src.selection.get_block_seed", return_value=42)
async def test_get_next_uids_normal_case(mock_seed):
    self = SimpleNamespace(
        miners=[DummyMiner(uid=i, ip="192.168.1.1") for i in range(10)],
        database=AsyncMock(),
        subtensor=object(),
    )
    self.database.get_selected_miners.return_value = [1, 2]

    result = await get_next_uids(self, "address", k=5)

    assert isinstance(result, list)
    assert len(result) == 5
    assert all(uid not in [1, 2] for uid in result)
    self.database.set_selection_miners.assert_called_once()


@pytest.mark.asyncio
@patch("subvortex.validator.neuron.src.selection.get_block_seed", return_value=42)
async def test_get_next_uids_with_retry(mock_seed):
    self = SimpleNamespace(
        miners=[DummyMiner(uid=i, ip="192.168.1.1") for i in range(3)],
        database=AsyncMock(),
        subtensor=object(),
    )
    self.database.get_selected_miners.return_value = []

    result = await get_next_uids(self, "retry_case", k=5)

    assert isinstance(result, list)
    assert len(result) <= 5
    self.database.set_selection_miners.assert_called_once()


@pytest.mark.asyncio
@patch("subvortex.validator.neuron.src.selection.get_block_seed", return_value=42)
async def test_get_next_uids_with_no_available_miners(mock_seed):
    self = SimpleNamespace(
        miners=[DummyMiner(uid=i, ip="0.0.0.0") for i in range(5)],
        database=AsyncMock(),
        subtensor=object(),
    )
    self.database.get_selected_miners.return_value = []

    result = await get_next_uids(self, "no_miners", k=5)

    assert result == []
    self.database.set_selection_miners.assert_called_once()
