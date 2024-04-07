from subnet.validator.score import compute_final_score

import tests.unit_tests.mocks.mock_miners as mocks


def test_a_miner_with_all_scores_equal_to_zero_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_verified
    miner.availability_score = 0
    miner.latency_score = 0
    miner.reliability_score = 0
    miner.distribution_score = 0

    # Act
    result = compute_final_score(miner)

    # Assert
    assert 0.0 == result


def test_a_miner_with_all_scores_not_equal_to_zero_should_return_a_score_of_zero():
    # Arrange
    miner = mocks.miner_verified
    miner.availability_score = 0.10
    miner.latency_score = 0.20
    miner.reliability_score = 0.30
    miner.distribution_score = 0.40

    expected_score = (3 * 0.10 + 0.20 + 0.30 + 0.40) / 6

    # Act
    result = compute_final_score(miner)

    # Assert
    assert expected_score == result
