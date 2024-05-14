from subnet.validator.score import compute_availability_score

import tests.unit_tests.mocks.mock_miners as mocks


def test_a_not_verified_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_1

    # Act
    result = compute_availability_score(miner)

    # Assert
    assert 0.0 == result


def test_a_suspicious_miner_with_no_penalise_factor_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_suspicious_1

    # Act
    result = compute_availability_score(miner)

    # Assert
    assert 0.0 == result


def test_a_suspicious_miner_with_a_penalty_factor_should_return_a_penalised_score():
    # Arrange
    miner = mocks.miner_suspicious_2

    # Act
    result = compute_availability_score(miner)

    # Assert
    assert 0.3 == result


def test_an_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_with_ip_conflicts_1

    # Act
    result = compute_availability_score(miner)

    # Assert
    assert 0.0 == result


def test_a_not_verified_and_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_and_ip_conflicts_1

    # Act
    result = compute_availability_score(miner)

    # Assert
    assert 0.0 == result


def test_a_verified_miner_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    # Act
    result = compute_availability_score(miner)

    # Assert
    assert 1.0 == result
