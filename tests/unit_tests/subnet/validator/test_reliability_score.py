import pytest

from subnet.validator.score import compute_reliability_score

import tests.unit_tests.mocks.mock_miners as mocks


@pytest.mark.asyncio
async def test_a_not_verified_miner_should_return_a_lowest_score():
    # Arrange
    reliability_score = mocks.miner_not_verified_1.reliability_score
    miner = mocks.miner_not_verified_1

    # Act
    result = await compute_reliability_score(miner)

    # Assert
    assert result < reliability_score


@pytest.mark.asyncio
async def test_a_not_verified_miner_should_return_updated_attempts_and_success_accordingly():
    # Arrange
    challenge_attempts = mocks.miner_not_verified_1.challenge_attempts
    challenge_successes = mocks.miner_not_verified_1.challenge_successes
    miner = mocks.miner_not_verified_1

    # Act
    await compute_reliability_score(miner)

    # Assert
    assert miner.challenge_attempts == challenge_attempts + 1
    assert miner.challenge_successes == challenge_successes


@pytest.mark.asyncio
async def test_an_ip_conflicts_miner_should_return_a_lowest_score():
    # Arrange
    reliability_score = mocks.miner_with_ip_conflicts_1.reliability_score
    miner = mocks.miner_with_ip_conflicts_1

    # Act
    result = await compute_reliability_score(miner)

    # Assert
    assert result < reliability_score


@pytest.mark.asyncio
async def test_an_ip_conflicts_miner_should_return_updated_attempts_and_success_accordingly():
    # Arrange
    challenge_attempts = mocks.miner_with_ip_conflicts_1.challenge_attempts
    challenge_successes = mocks.miner_with_ip_conflicts_1.challenge_successes
    miner = mocks.miner_with_ip_conflicts_1

    # Act
    await compute_reliability_score(miner)

    # Assert
    assert miner.challenge_attempts == challenge_attempts + 1
    assert miner.challenge_successes == challenge_successes


@pytest.mark.asyncio
async def test_a_not_verified_and_ip_conflicts_miner_should_return_a_lowest_score():
    # Arrange
    reliability_score = mocks.miner_not_verified_and_ip_conflicts_1.reliability_score
    miner = mocks.miner_not_verified_and_ip_conflicts_1

    # Act
    result = await compute_reliability_score(miner)

    # Assert
    assert result < reliability_score


@pytest.mark.asyncio
async def test_a_not_verified_and_ip_conflicts_miner_should_return_updated_attempts_and_success_accordingly():
    # Arrange
    challenge_attempts = mocks.miner_not_verified_and_ip_conflicts_1.challenge_attempts
    challenge_successes = mocks.miner_not_verified_and_ip_conflicts_1.challenge_successes
    miner = mocks.miner_not_verified_and_ip_conflicts_1

    # Act
    await compute_reliability_score(miner)

    # Assert
    assert miner.challenge_attempts == challenge_attempts + 1
    assert miner.challenge_successes == challenge_successes


@pytest.mark.asyncio
async def test_a_verified_miner_should_return_a_greater_score():
    # Arrange
    reliability_score = mocks.miner_verified.reliability_score
    miner = mocks.miner_verified

    # Act
    result = await compute_reliability_score(miner)

    # Assert
    assert result > reliability_score


@pytest.mark.asyncio
async def test_a_verified_miner_should_return_updated_attempts_and_success_accordingly():
    # Arrange
    challenge_attempts = mocks.miner_verified.challenge_attempts
    challenge_successes = mocks.miner_verified.challenge_successes
    miner = mocks.miner_verified

    # Act
    await compute_reliability_score(miner)

    # Assert
    assert miner.challenge_attempts == challenge_attempts + 1
    assert miner.challenge_successes == challenge_successes + 1
