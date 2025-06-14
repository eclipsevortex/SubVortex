# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex

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
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

import subvortex.validator.core.challenger.score as scoring
import subvortex.validator.core.challenger.constants as constants
import subvortex.validator.core.challenger.settings as sccs


class FakeSettings:
    def __init__(self):
        self.availability_weight = 1.0
        self.latency_weight = 1.0
        self.reliability_weight = 1.0
        self.distribution_weight = 1.0
        self.performance_weight = 1.0
        self.challenge_timeout = 10
        self.default_challenge_max_iteration = 10
        self.performance_reward_exponent = 1.0
        self.performance_penalty_factor = 0.5
        self.logging_name = "test"


class FakeMiner:
    def __init__(
        self,
        uid,
        hotkey,
        availability_successes=[1],
        reliability_successes=[1],
        latency_times=[1.0],
        performance_successes=[1],
        performance_boost=[1.0],
        distribution_score=1.0,
    ):
        self.uid = uid
        self.hotkey = hotkey
        self.availability_attempts = [1] * len(availability_successes)
        self.availability_successes = availability_successes
        self.reliability_attempts = [1] * len(reliability_successes)
        self.reliability_successes = reliability_successes
        self.latency_times = latency_times
        self.performance_attempts = [1] * len(performance_successes)
        self.performance_successes = performance_successes
        self.performance_boost = performance_boost
        self.distribution_score = distribution_score
        self.availability_score = 1.0
        self.latency_score = 1.0
        self.reliability_score = 1.0
        self.performance_score = 1.0


def make_fake_miners(count: int):
    return {
        f"hotkey_{i}": FakeMiner(
            uid=i,
            hotkey=f"hotkey_{i}",
            latency_times=[float(i + 1)],
            performance_boost=[1.0 / (i + 1)],
            distribution_score=np.exp(-0.5 * i),
        )
        for i in range(count)
    }


# Availability Score Tests
@pytest.mark.parametrize(
    "successes,expected",
    [
        ([1, 1, 1], 1.0),
        ([0, 0, 0], 0.0),
        ([1, 0, 1, 0], 0.5),
        ([1], 1.0),
        ([0], 0.0),
        ([], 0.0),
    ],
)
def test_compute_availability_score(successes, expected):
    miner = FakeMiner(uid=0, hotkey="hk", availability_successes=successes)
    miner.availability_attempts = [1] * len(successes)
    assert scoring.compute_availability_score(miner) == expected


# Reliability Score Tests
@pytest.mark.parametrize(
    "successes,expected",
    [
        ([1, 1, 1], 1.0),
        ([0, 0, 0], 0.0),
        ([1, 0, 1, 0], 0.5),
        ([1], 1.0),
        ([0], 0.0),
        ([], 0.0),
    ],
)
def test_compute_reliability_score(successes, expected):
    miner = FakeMiner(uid=0, hotkey="hk", reliability_successes=successes)
    miner.reliability_attempts = [1] * len(successes)
    assert scoring.compute_reliability_score(miner) == expected


# Latency Score
def test_compute_latency_score_valid_rank():
    settings = FakeSettings()
    miners = make_fake_miners(5)
    miner = miners["hotkey_2"]
    score = scoring.compute_latency_score(settings, miners, miner)
    assert 0 <= score <= 1


def test_compute_latency_score_invalid_hotkey():
    settings = FakeSettings()
    miners = make_fake_miners(5)
    invalid_miner = FakeMiner(uid=99, hotkey="invalid_hotkey")
    score = scoring.compute_latency_score(settings, miners, invalid_miner)
    assert score == constants.LATENCY_FAILURE_REWARD


def test_compute_latency_score_with_1_challenger_returns_lower_score():
    settings = FakeSettings()
    miners = {"hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", latency_times=[0.5])}
    miner = miners["hotkey_0"]
    score = scoring.compute_latency_score(settings, miners, miner)
    assert score == 0.737687106475089


def test_compute_latency_score_with_2_challengers_best_gets_high_score_but_not_1():
    settings = FakeSettings()
    miners = {
        "hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", latency_times=[0.5]),
        "hotkey_1": FakeMiner(uid=1, hotkey="hotkey_1", latency_times=[1.5]),
    }
    score = scoring.compute_latency_score(settings, miners, miners["hotkey_0"])
    assert score == 0.8688435532375445


def test_compute_latency_score_with_3_challengers_best_gets_full_score():
    settings = FakeSettings()
    miners = {
        "hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", latency_times=[0.5]),
        "hotkey_1": FakeMiner(uid=1, hotkey="hotkey_1", latency_times=[1.5]),
        "hotkey_2": FakeMiner(uid=2, hotkey="hotkey_2", latency_times=[2.5]),
    }
    score = scoring.compute_latency_score(settings, miners, miners["hotkey_0"])
    assert score == 1


# Performance Score
def test_compute_performance_score_success_vs_failure():
    success_miner = FakeMiner(uid=0, hotkey="hotkey_0", performance_successes=[1])
    failure_miner = FakeMiner(uid=1, hotkey="hotkey_1", performance_successes=[0])
    miners = {
        "hotkey_0": success_miner,
        "hotkey_1": failure_miner,
    }
    assert scoring.compute_performance_score(
        miners, success_miner
    ) > scoring.compute_performance_score(miners, failure_miner)


def test_compute_performance_score_invalid_hotkey():
    miners = make_fake_miners(5)
    invalid_miner = FakeMiner(uid=99, hotkey="invalid_hotkey")
    score = scoring.compute_performance_score(miners, invalid_miner)
    assert score == constants.PERFORMANCE_FAILURE_REWARD


def test_compute_performance_score_with_1_challenger_returns_lower_score():
    miners = {"hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", performance_boost=[1.0])}
    miner = miners["hotkey_0"]
    score = scoring.compute_performance_score(miners, miner)
    assert score == 0.737687106475089


def test_compute_performance_score_with_2_challengers_best_gets_high_score_but_not_1():
    miners = {
        "hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", performance_boost=[1.0]),
        "hotkey_1": FakeMiner(uid=1, hotkey="hotkey_1", performance_boost=[0.5]),
    }
    score = scoring.compute_performance_score(miners, miners["hotkey_0"])
    assert score == 0.8688435532375445


def test_compute_performance_score_with_3_challengers_best_gets_full_score():
    miners = {
        "hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", performance_boost=[1.0]),
        "hotkey_1": FakeMiner(uid=1, hotkey="hotkey_1", performance_boost=[0.5]),
        "hotkey_2": FakeMiner(uid=2, hotkey="hotkey_2", performance_boost=[0.25]),
    }
    score = scoring.compute_performance_score(miners, miners["hotkey_0"])
    assert score == 1


# Distribution Score
def test_compute_distribution_score_valid_rank():
    settings = FakeSettings()
    miners = make_fake_miners(5)
    top_miner = miners["hotkey_0"]
    score = scoring.compute_distribution_score(settings, miners, top_miner)
    assert score == scoring.compute_score(0)


def test_compute_distribution_score_invalid_hotkey():
    settings = FakeSettings()
    miners = make_fake_miners(5)
    invalid_miner = FakeMiner(uid=99, hotkey="invalid_hotkey")
    score = scoring.compute_distribution_score(settings, miners, invalid_miner)
    assert score == constants.DISTRIBUTION_FAILURE_REWARD


def test_distribution_score_top_rank_gets_highest_score():
    settings = FakeSettings()
    miners = {
        "hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", distribution_score=1.0),
        "hotkey_1": FakeMiner(
            uid=1, hotkey="hotkey_1", distribution_score=np.exp(-0.5)
        ),
        "hotkey_2": FakeMiner(uid=2, hotkey="hotkey_2", distribution_score=np.exp(-1)),
    }
    score_top = scoring.compute_distribution_score(settings, miners, miners["hotkey_0"])
    score_mid = scoring.compute_distribution_score(settings, miners, miners["hotkey_1"])
    score_low = scoring.compute_distribution_score(settings, miners, miners["hotkey_2"])
    assert score_top > score_mid > score_low
    assert score_top == pytest.approx(1.0)


def test_distribution_score_middle_rank_approximation():
    settings = FakeSettings()
    miners = {
        "hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", distribution_score=1.0),
        "hotkey_1": FakeMiner(
            uid=1, hotkey="hotkey_1", distribution_score=np.exp(-0.5)
        ),
        "hotkey_2": FakeMiner(uid=2, hotkey="hotkey_2", distribution_score=np.exp(-1)),
        "hotkey_3": FakeMiner(
            uid=3, hotkey="hotkey_3", distribution_score=np.exp(-1.5)
        ),
        "hotkey_4": FakeMiner(uid=4, hotkey="hotkey_4", distribution_score=np.exp(-2)),
    }
    mid = miners["hotkey_2"]
    score = scoring.compute_distribution_score(settings, miners, mid)
    expected = scoring.compute_score(2)
    assert score == pytest.approx(expected)


def test_distribution_score_invalid_hotkey_returns_failure_reward():
    settings = FakeSettings()
    miners = {
        "hotkey_0": FakeMiner(uid=0, hotkey="hotkey_0", distribution_score=1.0),
        "hotkey_1": FakeMiner(
            uid=1, hotkey="hotkey_1", distribution_score=np.exp(-0.5)
        ),
    }
    invalid_miner = FakeMiner(uid=99, hotkey="invalid_hotkey", distribution_score=1.0)
    score = scoring.compute_distribution_score(settings, miners, invalid_miner)
    assert score == constants.DISTRIBUTION_FAILURE_REWARD


# Final Score
def test_compute_final_score_with_default_and_overrides():
    settings = FakeSettings()
    miner = FakeMiner(uid=1, hotkey="hk")
    score_default = scoring.compute_final_score(settings, miner)
    score_with_overrides = scoring.compute_final_score(
        settings, miner, {"availability": 0.0, "latency": 0.0}
    )
    assert score_default > score_with_overrides


def test_compute_score_decay_function():
    scores = [scoring.compute_score(i) for i in range(5)]
    for earlier, later in zip(scores, scores[1:]):
        assert earlier > later


# Refresh Metadata (mocked)
@patch("subvortex.validator.core.challenger.utils.apply_sma")
def test_refresh_availability_metadata(mock_sma):
    settings = FakeSettings()
    result = type("ChallengeResult", (), {"is_available": True})()
    miner = FakeMiner(uid=1, hotkey="hk")
    mock_sma.side_effect = lambda *_: [1]
    attempts, successes = scoring.refresh_availability_metadata(settings, result, miner)
    assert attempts == [1]
    assert successes == [1]


@patch("subvortex.validator.core.challenger.utils.apply_sma")
def test_refresh_reliability_metadata(mock_sma):
    settings = FakeSettings()
    result = type("ChallengeResult", (), {"is_reliable": True})()
    miner = FakeMiner(uid=1, hotkey="hk")
    mock_sma.side_effect = lambda *_: [1]
    attempts, successes = scoring.refresh_reliability_metadata(settings, result, miner)
    assert attempts == [1]
    assert successes == [1]


@patch("subvortex.validator.core.challenger.utils.apply_sma")
def test_refresh_reliability_metadata(mock_sma):
    settings = FakeSettings()
    result = type("ChallengeResult", (), {"is_reliable": True})()
    miner = FakeMiner(uid=1, hotkey="hk")
    mock_sma.side_effect = lambda *_: [1]
    attempts, successes = scoring.refresh_reliability_metadata(settings, result, miner)
    assert attempts == [1]
    assert successes == [1]


@patch("subvortex.validator.core.challenger.utils.apply_sma")
def test_refresh_latency_metadata(mock_sma):
    settings = FakeSettings()
    result = type("ChallengeResult", (), {"avg_process_time": 2.0})()
    miner = FakeMiner(uid=1, hotkey="hk")
    mock_sma.return_value = [2.0]
    latency_times = scoring.refresh_latency_metadata(settings, result, miner)
    assert latency_times == [2.0]


@patch("subvortex.validator.core.challenger.utils.apply_sma")
def test_refresh_performance_metadata(mock_sma):
    settings = FakeSettings()
    result = type(
        "ChallengeResult", (), {"challenge_attempts": 5, "challenge_successes": 4}
    )()
    miner = FakeMiner(uid=1, hotkey="hk")
    mock_sma.side_effect = [[5], [4], [0.9]]
    attempts, successes, boosts = scoring.refresh_performance_metadata(
        settings, result, miner
    )
    assert attempts == [5]
    assert successes == [4]
    assert boosts == [0.9]


@patch("subvortex.validator.core.challenger.utils.apply_sma")
def test_refresh_performance_metadata(mock_sma):
    settings = FakeSettings()
    result = type(
        "ChallengeResult", (), {"challenge_attempts": 5, "challenge_successes": 4}
    )()
    miner = FakeMiner(uid=1, hotkey="hk")
    mock_sma.side_effect = [[5], [4], [0.9]]
    attempts, successes, boosts = scoring.refresh_performance_metadata(
        settings, result, miner
    )
    assert attempts == [5]
    assert successes == [4]
    assert boosts == [0.9]
