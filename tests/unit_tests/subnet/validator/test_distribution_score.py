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
