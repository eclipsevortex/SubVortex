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
from subvortex.validator.neuron.src.score import compute_final_score

import subvortex.validator.neuron.tests.mock.mock_miners as mocks


def test_a_not_verified_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_verified
    miner.verified = False
    miner.sync = False
    miner.availability_score = 0
    miner.latency_score = 0
    miner.reliability_score = 0
    miner.distribution_score = 0

    # Act
    result = compute_final_score(miner)

    # Assert
    assert 0.0 == result


def test_a_not_sync_miner_should_return_a_score_different_of_zero():
    # Arrange
    miner = mocks.miner_verified
    miner.verified = True
    miner.sync = False
    miner.availability_score = 0.10
    miner.latency_score = 0.20
    miner.reliability_score = 0.30
    miner.distribution_score = 0.40

    expected_score = (0.10 * 3 + 0.20 * 7 + 0.30 * 3 + 0.40 * 2) / 15

    # Act
    result = compute_final_score(miner)

    # Assert
    assert expected_score == result


def test_a_suspicious_miner_with_no_penalty_factor_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_suspicious_1
    miner.verified = True
    miner.sync = False
    miner.availability_score = 0.10
    miner.latency_score = 0.20
    miner.reliability_score = 0.30
    miner.distribution_score = 0.40

    # Act
    result = compute_final_score(miner)

    # Assert
    assert 0 == result


def test_a_suspicious_miner_with_penalty_factor_should_return_a_score_different_of_zero():
    # Arrange
    miner = mocks.miner_suspicious_2
    miner.verified = True
    miner.sync = False
    miner.availability_score = 0.10
    miner.latency_score = 0.20
    miner.reliability_score = 0.30
    miner.distribution_score = 0.40
    miner.penalty_factor = 0.4

    expected_score = ((0.10 * 3 + 0.20 * 7 + 0.30 * 3 + 0.40 * 2) / 15) * 0.4

    # Act
    result = compute_final_score(miner)

    # Assert
    assert expected_score == result


def test_a_verified_and_sync_miner_should_return_a_score_different_of_zero():
    # Arrange
    miner = mocks.miner_verified
    miner.verified = True
    miner.sync = True
    miner.availability_score = 0.10
    miner.latency_score = 0.20
    miner.reliability_score = 0.30
    miner.distribution_score = 0.40

    expected_score = (0.10 * 8 + 0.20 * 7 + 0.30 * 3 + 0.40 * 2) / 20

    # Act
    result = compute_final_score(miner)

    # Assert
    assert expected_score == result
