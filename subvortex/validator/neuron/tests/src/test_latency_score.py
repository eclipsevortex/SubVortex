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
from subvortex.validator.neuron.src.score import compute_latency_score

import subvortex.validator.neuron.tests.mock.mock_miners as mocks

locations = {
    "DE": {"country": "Germany", "latitude": 51.165691, "longitude": 10.451526},
}


def test_a_not_verified_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_1

    # Act
    result = compute_latency_score(miner.country, miner, [miner], locations, False)

    # Assert
    assert 0.0 == result


def test_an_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_with_ip_conflicts_1

    # Act
    result = compute_latency_score(miner.country, miner, [miner], locations, True)

    # Assert
    assert 0.0 == result


def test_a_not_verified_and_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_and_ip_conflicts_1

    # Act
    result = compute_latency_score(miner.country, miner, [miner], locations, True)

    # Assert
    assert 0.0 == result


def test_a_verified_miner_when_alone_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_are_not_verified_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [
        miner,
        mocks.miner_not_verified_and_ip_conflicts_1,
        mocks.miner_not_verified_and_ip_conflicts_2,
    ]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_have_ip_conflicts_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner, mocks.miner_with_ip_conflicts_1, mocks.miner_with_ip_conflicts_2]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_are_not_verified_and_have_ip_conflicts_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner, mocks.miner_with_ip_conflicts_1, mocks.miner_with_ip_conflicts_2]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_evaluating_the_best_one_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_with_best_latency
    miners = [
        mocks.miner_with_best_latency,
        mocks.miner_with_in_between_latency,
        mocks.miner_with_worst_latency,
    ]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_evaluating_the_worst_one_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_with_worst_latency
    miners = [
        mocks.miner_with_best_latency,
        mocks.miner_with_in_between_latency,
        mocks.miner_with_worst_latency,
    ]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 0.0 == result


def test_a_verified_miner_when_evaluating_a_middle_one_should_return_a_score_between_zero_and_one():
    # Arrange
    miner = mocks.miner_with_in_between_latency
    miners = [
        mocks.miner_with_best_latency,
        mocks.miner_with_in_between_latency,
        mocks.miner_with_worst_latency,
    ]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 0.5 == result


def test_a_verified_miner_when_evaluating_a_30_percent_close_to_the_best_should_return_a_score_between_zero_and_one():
    # Arrange
    miner = mocks.miner_with_30_percent_to_the_best_in_between_latency
    miners = [
        mocks.miner_with_best_latency,
        mocks.miner_with_30_percent_to_the_best_in_between_latency,
        mocks.miner_with_worst_latency,
    ]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert 0.7 == result


def test_a_verified_miner_when_evaluating_a_30_percent_close_to_the_worst_should_return_a_score_between_zero_and_one():
    # Arrange
    miner = mocks.miner_with_30_percent_to_the_worst_in_between_latency
    miners = [
        mocks.miner_with_best_latency,
        mocks.miner_with_30_percent_to_the_worst_in_between_latency,
        mocks.miner_with_worst_latency,
    ]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations, False)

    # Assert
    assert abs(0.3 - result) < 0.000000000000001