from subnet.validator.score import compute_final_score

import tests.unit_tests.mocks.mock_miners as mocks


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
