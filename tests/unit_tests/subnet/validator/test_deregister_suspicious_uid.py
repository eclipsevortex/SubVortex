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
import copy

from subnet.validator.utils import deregister_suspicious_uid

from tests.unit_tests.test_case import TestCase
from tests.unit_tests.mocks import mock_miners


class TestDeregisterSuspiciousUid(TestCase):
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