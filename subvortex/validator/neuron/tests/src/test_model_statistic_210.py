import pytest
import asyncio
from unittest.mock import AsyncMock
from subvortex.validator.neuron.src.models.statistics import StatisticModel210 as StatisticModel


@pytest.mark.asyncio
async def test_statistic_model_210_uses_new_redis_key():
    # Arrange
    ss58_address = "test123"
    expected_key = f"sv:stats:{ss58_address}"
    model = StatisticModel()

    # Mock Redis client
    redis_mock = AsyncMock()

    # Sample data to write
    input_data = {
        "country": "US",
        "verified": True,
        "score": 0.75,
        "availability_score": 0.9,
        "latency_score": 0.8,
        "reliability_score": 0.7,
        "distribution_score": 0.6,
        "challenge_successes": 5,
        "challenge_attempts": 10,
        "process_time": 1.23,
    }

    # Act
    await model.write(redis_mock, ss58_address, input_data)

    # Assert
    redis_mock.hset.assert_called_once()
    assert redis_mock.hset.call_args.kwargs["mapping"]["country"] == "US"
    assert redis_mock.hset.call_args.kwargs["mapping"]["verified"] == "True"
    assert redis_mock.hset.call_args.kwargs["mapping"]["score"] == "0.75"
    assert redis_mock.hset.call_args.args[0] == expected_key

    # Prepare mock return for read test
    redis_mock.hgetall.return_value = {
        b"country": b"US",
        b"version": b"2.1.0",
        b"verified": b"1",
        b"score": b"0.75",
        b"availability_score": b"0.9",
        b"latency_score": b"0.8",
        b"reliability_score": b"0.7",
        b"distribution_score": b"0.6",
        b"challenge_successes": b"5",
        b"challenge_attempts": b"10",
        b"process_time": b"1.23",
    }

    # Act
    result = await model.read(redis_mock, ss58_address)

    # Assert
    redis_mock.hgetall.assert_called_once_with(expected_key)
    assert result["country"] == "US"
    assert result["verified"] is True
    assert result["score"] == 0.75
