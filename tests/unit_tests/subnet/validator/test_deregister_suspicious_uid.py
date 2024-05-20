import copy
import unittest

from subnet.validator.utils import deregister_suspicious_uid

from tests.unit_tests.mocks import mock_miners


class TestDeregisterSuspiciousUid(unittest.TestCase):
    def test_a_miner_not_suspicious_should_return_the_initial_score(
        self,
    ):
        # Arrange
        miner = copy.deepcopy(mock_miners.miner_verified)
        miner.uid = 0

        miners = [miner]
        moving_averaged_scores = [0.5]

        # Act
        deregister_suspicious_uid(miners, moving_averaged_scores)

        # Assert
        assert 0.5 == moving_averaged_scores[miner.uid]

    def test_a_suspicious_miner_without_penalty_factor_should_return_a_score_of_zero(
        self,
    ):
        # Arrange
        miner = copy.deepcopy(mock_miners.miner_verified)
        miner.uid = 0

        miners = [miner]
        moving_averaged_scores = [0.5]

        miners[miner.uid].suspicious = True

        # Act
        deregister_suspicious_uid(miners, moving_averaged_scores)

        # Assert
        assert 0 == moving_averaged_scores[miner.uid]

    def test_a_suspicious_miner_with_penalty_factor_should_return_a_penalised_score(
        self,
    ):
        # Arrange
        miner = copy.deepcopy(mock_miners.miner_verified)
        miner.uid = 0

        miners = [miner]
        moving_averaged_scores = [0.5]

        miners[miner.uid].suspicious = True
        miners[miner.uid].penalty_factor = 0.3

        # Act
        deregister_suspicious_uid(miners, moving_averaged_scores)

        # Assert
        assert 0.15 == moving_averaged_scores[miner.uid]
