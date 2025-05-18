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
from subvortex.validator.neuron.tests.mock.mock_miners import miner_verified

from subvortex.validator.neuron.src.security import is_miner_suspicious


def test_given_no_penalty_factor_when_miner_uid_and_hotkey_has_no_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [
        {"uid": 2, "hotkey": "5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd82"}
    ]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == is_suspicious
    assert 0 == penalty_factor


def test_given_no_penalty_factor_when_miner_uid_and_hotkey_has_a_match_in_the_suspicious_list_should_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [{"uid": miner.uid, "hotkey": miner.hotkey}]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert True == is_suspicious
    assert 0 == penalty_factor


def test_given_no_penalty_factor_when_miner_uid_but_not_hotkey_has_a_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [
        {"uid": miner.uid, "hotkey": "5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd82"}
    ]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == is_suspicious
    assert 0 == penalty_factor


def test_given_no_penalty_factor_when_miner_hotkey_but_not_uid_has_a_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [{"uid": 2, "hotkey": miner.hotkey}]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == is_suspicious
    assert 0 == penalty_factor


def test_given_penalty_factor_when_miner_uid_and_hotkey_has_no_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [
        {
            "uid": 2,
            "hotkey": "5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd82",
            "penalty_factor": 0.3,
        }
    ]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == is_suspicious
    assert 0 == penalty_factor


def test_given_penalty_factor_when_miner_uid_and_hotkey_has_a_match_in_the_suspicious_list_should_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [
        {"uid": miner.uid, "hotkey": miner.hotkey, "penalty_factor": 0.3}
    ]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert True == is_suspicious
    assert 0.3 == penalty_factor


def test_given_penalty_factor_when_miner_uid_but_not_hotkey_has_a_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [
        {
            "uid": miner.uid,
            "hotkey": "5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd82",
            "penalty_factor": 0.3,
        }
    ]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == is_suspicious
    assert 0 == penalty_factor


def test_given_penalty_factor_when_miner_hotkey_but_not_uid_has_a_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [{"uid": 2, "hotkey": miner.hotkey, "penalty_factor": 0.3}]

    # Act
    is_suspicious, penalty_factor = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == is_suspicious
    assert 0 == penalty_factor