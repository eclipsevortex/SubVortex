# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex
# [license text omitted for brevity]

import pytest
from subvortex.validator.neuron.src.score import compute_reliability_score
import subvortex.validator.neuron.tests.mock.mock_miners as mocks


@pytest.mark.asyncio
async def test_unverified_miner_should_get_penalty():
    miner = mocks.miner_not_verified_1
    result = await compute_reliability_score(miner, has_ip_conflicts=False)
    assert 0 < result <= 1, "❌ Expected reliability score between 0 and 1 for verified miner"


@pytest.mark.asyncio
async def test_ip_conflict_miner_should_get_penalty():
    miner = mocks.miner_with_ip_conflicts_1
    result = await compute_reliability_score(miner, has_ip_conflicts=True)
    assert result == pytest.approx(0.0), "❌ Expected penalty for miner with IP conflict"


@pytest.mark.asyncio
async def test_unverified_and_ip_conflict_miner_should_get_penalty():
    miner = mocks.miner_not_verified_and_ip_conflicts_1
    result = await compute_reliability_score(miner, has_ip_conflicts=True)
    assert result == pytest.approx(0.0), "❌ Expected penalty for unverified + IP conflict"


@pytest.mark.asyncio
async def test_verified_miner_should_get_positive_score():
    miner = mocks.miner_verified
    result = await compute_reliability_score(miner, has_ip_conflicts=False)
    assert 0 < result <= 1, "❌ Expected reliability score between 0 and 1 for verified miner"
