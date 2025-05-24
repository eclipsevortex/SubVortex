import numpy as np
from unittest.mock import MagicMock, patch

import bittensor_wallet.wallet as btw

from subvortex.validator.neuron.src.settings import Settings
from subvortex.validator.neuron.src.weights import should_set_weights, set_weights


def test_should_set_weights_allows_after_interval():
    subtensor = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    subtensor.weights_rate_limit.return_value = 5

    # Simulate list of last update blocks
    last_updates = [0] * 43
    last_updates[42] = 10
    subtensor.get_hyperparameter.return_value = last_updates

    current_block = 16  # 10 + 5 + 1 == 16 → OK
    assert should_set_weights(settings, subtensor, uid=42, block=current_block)


def test_should_set_weights_disallows_before_limit():
    subtensor = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    subtensor.weights_rate_limit.return_value = 5

    last_updates = [0] * 43
    last_updates[42] = 12
    subtensor.get_hyperparameter.return_value = last_updates

    current_block = 16  # 12 + 5 + 1 = 18 → too early
    assert not should_set_weights(settings, subtensor, uid=42, block=current_block)


def test_should_set_weights_missing_uid_defaults_to_zero():
    subtensor = MagicMock()
    settings = Settings(netuid=1, logging_name="validator")
    subtensor.weights_rate_limit.return_value = 2

    # Empty list simulates uid 42 being out of range
    subtensor.get_hyperparameter.return_value = []
    current_block = 3  # 0 + 2 + 1 = 3
    assert should_set_weights(settings, subtensor, uid=42, block=current_block)


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

    set_weights(settings, subtensor, wallet, uid=42, moving_scores=scores)

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

    # First try: fails, second try: succeeds
    subtensor.blocks_since_last_update.side_effect = [10, 10, 5, 5]
    subtensor.set_weights.side_effect = [
        (False, "temporary failure"),
        (True, "Success"),
    ]

    set_weights(settings, subtensor, wallet, uid=42, moving_scores=scores)

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

    set_weights(settings, subtensor, wallet, uid=42, moving_scores=scores)

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

    set_weights(settings, subtensor, wallet, uid=42, moving_scores=scores)

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
        set_weights(settings, subtensor, wallet, uid=42, moving_scores=scores)
    except Exception as e:
        assert str(e) == "Invalid input"
