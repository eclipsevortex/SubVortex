from tests.unit_tests.mocks.mock_miners import miner_verified

from subnet.validator.security import is_miner_suspicious


def test_miner_uid_and_hotkey_has_no_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [
        {"uid": 2, "hotkey": "5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd82"}
    ]

    # Act
    result = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == result


def test_miner_uid_and_hotkey_has_a_match_in_the_suspicious_list_should_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [{"uid": miner.uid, "hotkey": miner.hotkey}]

    # Act
    result = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert True == result


def test_miner_uid_but_not_hotkey_has_a_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [
        {"uid": miner.uid, "hotkey": "5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd82"}
    ]

    # Act
    result = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == result


def test_miner_hotkey_but_not_uid_has_a_match_in_the_suspicious_list_should_not_be_flagged_as_suspicious():
    # Arrange
    miner = miner_verified
    suspicious_uids = [{"uid": 2, "hotkey": miner.hotkey}]

    # Act
    result = is_miner_suspicious(miner, suspicious_uids)

    # Assert
    assert False == result
