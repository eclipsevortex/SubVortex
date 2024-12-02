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
from subnet.validator.score import compute_distribution_score

import tests.unit_tests.mocks.mock_miners as mocks


def test_a_not_verified_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_1

    # Act
    result = compute_distribution_score(miner, [miner])

    # Assert
    assert 0.0 == result


def test_an_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_with_ip_conflicts_1

    # Act
    result = compute_distribution_score(miner, [miner])

    # Assert
    assert 0.0 == result


def test_a_not_verified_and_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_and_ip_conflicts_1

    # Act
    result = compute_distribution_score(miner, [miner])

    # Assert
    assert 0.0 == result


def test_a_verified_miner_when_alone_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner]

    # Act
    result = compute_distribution_score(miner, miners)

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
    result = compute_distribution_score(miner, miners)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_have_ip_conflicts_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner, mocks.miner_with_ip_conflicts_1, mocks.miner_with_ip_conflicts_2]

    # Act
    result = compute_distribution_score(miner, miners)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_are_not_verified_and_have_ip_conflicts_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner, mocks.miner_with_ip_conflicts_1, mocks.miner_with_ip_conflicts_2]

    # Act
    result = compute_distribution_score(miner, miners)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_are_not_in_the_same_location_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_unique_localisation

    miners = [
        miner,
        mocks.miner_gb_1,
        mocks.miner_gb_2,
    ]

    # Act
    result = compute_distribution_score(miner, miners)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_its_location_is_share_with_some_other_miners_should_return_a_distributed_score():
    # Arrange
    miner = mocks.miner_gb_1

    miners = [
        miner,
        mocks.miner_verified,
        mocks.miner_gb_2,
    ]

    # Act
    result = compute_distribution_score(miner, miners)

    # Assert
    assert 0.5 == result
