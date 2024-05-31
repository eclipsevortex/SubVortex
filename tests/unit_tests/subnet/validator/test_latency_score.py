from subnet.validator.score import compute_latency_score

import tests.unit_tests.mocks.mock_miners as mocks

locations = {
    "DE": {"country": "Germany", "latitude": 51.165691, "longitude": 10.451526},
}


def test_a_not_verified_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_1

    # Act
    result = compute_latency_score(miner.country, miner, [miner], locations)

    # Assert
    assert 0.0 == result


def test_an_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_with_ip_conflicts_1

    # Act
    result = compute_latency_score(miner.country, miner, [miner], locations)

    # Assert
    assert 0.0 == result


def test_a_not_verified_and_ip_conflicts_miner_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_not_verified_and_ip_conflicts_1

    # Act
    result = compute_latency_score(miner.country, miner, [miner], locations)

    # Assert
    assert 0.0 == result


def test_a_verified_miner_when_alone_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations)

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
    result = compute_latency_score(miner.country, miner, miners, locations)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_have_ip_conflicts_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner, mocks.miner_with_ip_conflicts_1, mocks.miner_with_ip_conflicts_2]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations)

    # Assert
    assert 1.0 == result


def test_a_verified_miner_when_other_miners_are_not_verified_and_have_ip_conflicts_should_return_a_score_of_one():
    # Arrange
    miner = mocks.miner_verified

    miners = [miner, mocks.miner_with_ip_conflicts_1, mocks.miner_with_ip_conflicts_2]

    # Act
    result = compute_latency_score(miner.country, miner, miners, locations)

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
    result = compute_latency_score(miner.country, miner, miners, locations)

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
    result = compute_latency_score(miner.country, miner, miners, locations)

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
    result = compute_latency_score(miner.country, miner, miners, locations)

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
    result = compute_latency_score(miner.country, miner, miners, locations)

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
    result = compute_latency_score(miner.country, miner, miners, locations)

    # Assert
    assert abs(0.3 - result) < 0.000000000000001
