import numpy as np
from unittest.mock import MagicMock, patch
import bittensor_wallet.wallet as btw

from subvortex.core.model.neuron import Neuron
from subvortex.validator.neuron.src.settings import Settings
from subvortex.validator.neuron.src.weights import (
    should_set_weights,
    set_weights,
    reset_scores_for_not_serving_miners,
)
from subvortex.validator.neuron.src.models.miner import Miner


def test_should_set_weights_allows_after_interval():
    subtensor = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    subtensor.weights_rate_limit.return_value = 5

    neuron = Neuron(uid=42, stake=100)
    last_updates = [0] * 43
    last_updates[42] = 10
    subtensor.get_hyperparameter.return_value = last_updates

    current_block = 16  # 10 + 5 + 1 = 16
    min_stake = 10

    assert should_set_weights(settings, subtensor, neuron, current_block, min_stake)


def test_should_set_weights_disallows_before_limit():
    subtensor = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    subtensor.weights_rate_limit.return_value = 5

    neuron = Neuron(uid=42, stake=100)
    last_updates = [0] * 43
    last_updates[42] = 12
    subtensor.get_hyperparameter.return_value = last_updates

    current_block = 16  # 12 + 5 + 1 = 18 → too early
    min_stake = 10

    assert not should_set_weights(settings, subtensor, neuron, current_block, min_stake)


def test_should_set_weights_missing_uid_defaults_to_zero():
    subtensor = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    subtensor.weights_rate_limit.return_value = 2

    neuron = Neuron(uid=42, stake=100)
    subtensor.get_hyperparameter.return_value = []
    current_block = 3  # 0 + 2 + 1 = 3
    min_stake = 10

    assert should_set_weights(settings, subtensor, neuron, current_block, min_stake)


def test_should_set_weights_rejects_low_stake():
    subtensor = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    subtensor.weights_rate_limit.return_value = 2

    neuron = Neuron(uid=1, stake=5)
    last_updates = [0] * 10
    last_updates[1] = 0
    subtensor.get_hyperparameter.return_value = last_updates

    current_block = 10
    min_stake = 10

    assert not should_set_weights(settings, subtensor, neuron, current_block, min_stake)


@patch("subvortex.validator.neuron.src.weights.scbs.process_weights_for_netuid")
@patch("subvortex.validator.neuron.src.weights.btul.logging")
def test_set_weights_success_first_try(mock_log, mock_process):
    subtensor = MagicMock()
    wallet = MagicMock(spec=btw.Wallet)
    settings = Settings(netuid=1, logging_name="validator")

    uids = np.array([0, 1, 2])
    scores = np.array([0.4, 0.3, 0.3])
    mock_process.return_value = (uids, scores)

    subtensor.blocks_since_last_update.return_value = 5
    subtensor.set_weights.return_value = (True, "Success")

    set_weights(settings, subtensor, wallet, uid=42, weights=scores, version="1.0.0")

    subtensor.set_weights.assert_called_once()
    mock_log.success.assert_called()


@patch("subvortex.validator.neuron.src.weights.scbs.process_weights_for_netuid")
@patch("subvortex.validator.neuron.src.weights.btul.logging")
def test_set_weights_success_after_retry(mock_log, mock_process):
    subtensor = MagicMock()
    wallet = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    settings.weights_setting_attempts = 2

    uids = np.array([0, 1, 2])
    scores = np.array([0.4, 0.3, 0.3])
    mock_process.return_value = (uids, scores)

    subtensor.blocks_since_last_update.side_effect = [10, 10, 5, 5]
    subtensor.set_weights.side_effect = [
        (False, "temporary failure"),
        (True, "Success"),
    ]

    set_weights(settings, subtensor, wallet, uid=42, weights=scores, version="1.0.0")

    assert subtensor.set_weights.call_count == 2
    assert mock_log.success.call_count == 1


@patch("subvortex.validator.neuron.src.weights.scbs.process_weights_for_netuid")
@patch("subvortex.validator.neuron.src.weights.btul.logging")
def test_set_weights_succeeds_due_to_block_change(mock_log, mock_process):
    subtensor = MagicMock()
    wallet = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    settings.weights_setting_attempts = 1

    uids = np.array([0, 1])
    scores = np.array([0.5, 0.5])
    mock_process.return_value = (uids, scores)

    subtensor.blocks_since_last_update.side_effect = [10, 9]
    subtensor.set_weights.return_value = (False, "No inclusion")

    set_weights(settings, subtensor, wallet, uid=42, weights=scores, version="1.0.0")

    mock_log.success.assert_called_once()
    mock_log.warning.assert_not_called()


@patch("subvortex.validator.neuron.src.weights.scbs.process_weights_for_netuid")
@patch("subvortex.validator.neuron.src.weights.btul.logging")
def test_set_weights_all_attempts_fail(mock_log, mock_process):
    subtensor = MagicMock()
    wallet = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    settings.weights_setting_attempts = 2

    uids = np.array([0])
    scores = np.array([1.0])
    mock_process.return_value = (uids, scores)

    subtensor.blocks_since_last_update.side_effect = [10, 10, 10, 10]
    subtensor.set_weights.side_effect = [
        (False, "net error"),
        (False, "timeout"),
    ]

    set_weights(settings, subtensor, wallet, uid=42, weights=scores, version="1.0.0")

    assert subtensor.set_weights.call_count == 2
    mock_log.error.assert_called_once()
    assert "after 2 attempts" in mock_log.error.call_args[0][0]


@patch("subvortex.validator.neuron.src.weights.scbs.process_weights_for_netuid")
def test_set_weights_handles_weight_processing_error(mock_process):
    subtensor = MagicMock()
    wallet = MagicMock()
    settings = Settings(netuid=1, logging_name="validator", weights_setting_attempts=1)

    scores = np.array([0.5, 0.5])
    mock_process.side_effect = Exception("Invalid input")

    try:
        set_weights(settings, subtensor, wallet, uid=42, weights=scores, version="1.0.0")
    except Exception as e:
        assert str(e) == "Invalid input"


def test_all_good_miners_keep_scores():
    scores = np.random.rand(256)
    miners = [Miner(uid=i, ip="1.2.3.4") for i in range(256)]
    reset_miners = []

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)
    np.testing.assert_array_equal(result, scores)


def test_miner_with_0_ip_gets_zeroed():
    scores = np.random.rand(256)
    miners = [Miner(uid=i, ip="0.0.0.0" if i == 42 else "1.2.3.4") for i in range(256)]
    reset_miners = []

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    assert result[42] == 0.0
    for i in range(256):
        if i != 42:
            assert result[i] == scores[i]


def test_reset_miners_also_get_zeroed():
    scores = np.random.rand(256)
    miners = [Miner(uid=i, ip="1.2.3.4") for i in range(256)]
    reset_miners = [Miner(uid=42, ip="1.2.3.4")]

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    assert result[42] == 0.0
    for i in range(256):
        if i != 42:
            assert result[i] == scores[i]


def test_uid_missing_from_miners_gets_zeroed():
    scores = np.random.rand(256)
    # Only include miners for a subset of UIDs (e.g. exclude UID 42)
    miners = [Miner(uid=i, ip="1.2.3.4") for i in range(256) if i != 42]
    reset_miners = []

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    assert result[42] == 0.0  # UID 42 not in miners, should be zeroed
    for i in range(256):
        if i != 42:
            assert result[i] == scores[i]


def test_reset_miners_not_in_main_list_still_get_zeroed():
    scores = np.random.rand(256)
    miners = [Miner(uid=i, ip="1.2.3.4") for i in range(256)]
    reset_miners = [Miner(uid=300, ip="1.2.3.4")]

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    for i in range(256):
        assert result[i] == scores[i]


def test_empty_miners_and_empty_reset_miners_zeros_all():
    scores = np.random.rand(256)
    result = reset_scores_for_not_serving_miners([], scores, [])
    assert np.all(result == 0.0)


def test_empty_miners_with_reset_miners_zeros_resets_only():
    scores = np.random.rand(256)
    miners = [Miner(uid=i, ip="1.2.3.4") for i in range(256) if i not in [5, 12]]
    reset_miners = [Miner(uid=5, ip="1.2.3.4"), Miner(uid=12, ip="1.2.3.4")]
    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    for i in range(256):
        if i in [5, 12]:
            assert result[i] == 0.0
        else:
            assert result[i] == scores[i]


def test_out_of_bounds_uid_skipped():
    scores = np.random.rand(256)
    original = scores.copy()

    miners = [Miner(uid=i, ip="1.2.3.4") for i in range(256)]
    miners += [Miner(uid=300, ip="1.2.3.4")]  # out-of-bounds
    reset_miners = []

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    # Expect no change at all
    np.testing.assert_array_equal(result, original)


def test_out_of_bounds_uid_ignored_while_valid_bad_ip_zeroed():
    scores = np.random.rand(256)
    miners = [
        Miner(uid=5, ip="0.0.0.0") if i == 5 else Miner(uid=i, ip="1.2.3.4")
        for i in range(256)
    ]
    miners += [Miner(uid=300, ip="1.2.3.4")]  # out-of-bounds
    reset_miners = []

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    assert result[5] == 0.0
    for i in range(256):
        if i != 5:
            assert result[i] == scores[i]


def test_original_array_not_mutated():
    scores = np.random.rand(256)
    original = scores.copy()
    miners = [Miner(uid=123, ip="0.0.0.0")]
    reset_miners = []

    _ = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    np.testing.assert_array_equal(scores, original)


def test_duplicate_uids_in_reset_and_bad_ip_only_zero_once():
    scores = np.random.rand(256)
    miners = [Miner(uid=i, ip="0.0.0.0" if i == 42 else "1.2.3.4") for i in range(256)]
    reset_miners = [Miner(uid=42, ip="1.2.3.4")]

    result = reset_scores_for_not_serving_miners(miners, scores, reset_miners)

    assert result[42] == 0.0
    for i in range(256):
        if i != 42:
            assert result[i] == scores[i]
