import os
import pytest
import numpy as np
from subvortex.validator.neuron.src.state import load_state, save_state


# Dummy classes to simulate required structure
class DummyConfig:
    class Neuron:
        full_path = ""

    neuron = Neuron()


class Dummy:
    def __init__(self, path, scores_shape):
        self.config = DummyConfig()
        self.config.neuron.full_path = path
        self.moving_scores = np.zeros(scores_shape)

    def load_state(self, number_of_neurons):
        self.moving_scores = load_state(self.config.neuron.full_path, number_of_neurons)

    def save_state(self):
        save_state(self.config.neuron.full_path, self.moving_scores)


# Fixture to setup temporary directory and model path
@pytest.fixture
def setup_tmp_path(tmp_path):
    path = tmp_path / "model.npz"
    return tmp_path, path


# Test loading state with correct shape
def test_load_state_success_matching_shape(setup_tmp_path):
    # Arrange
    tmp_path, dummy_file = setup_tmp_path
    weights = np.random.rand(10)
    np.savez(dummy_file, neuron_weights=weights)
    obj = Dummy(str(tmp_path), 10)

    # Act
    obj.load_state(10)

    # Assert
    assert np.allclose(obj.moving_scores, weights)


# Test loading state with mismatched shape
def test_load_state_success_mismatched_shape(setup_tmp_path):
    # Arrange
    tmp_path, dummy_file = setup_tmp_path
    weights = np.random.rand(5)
    np.savez(dummy_file, neuron_weights=weights)
    obj = Dummy(str(tmp_path), 10)

    # Act
    obj.load_state(10)

    # Assert
    assert np.allclose(obj.moving_scores[:5], weights)
    assert np.all(obj.moving_scores[5:] == 0.0)


# Test loading state with NaN values
def test_load_state_nan_weights(setup_tmp_path):
    # Arrange
    tmp_path, dummy_file = setup_tmp_path
    weights = np.array([0.1, np.nan, 0.3])
    np.savez(dummy_file, neuron_weights=weights)
    obj = Dummy(str(tmp_path), 3)

    # Act
    obj.load_state(3)

    # Assert
    assert np.all(obj.moving_scores == 0.0)


# Test when state file is not found
def test_load_state_file_not_found(tmp_path):
    # Arrange
    obj = Dummy(str(tmp_path), 3)

    # Act
    obj.load_state(3)

    # Assert
    assert np.all(obj.moving_scores == 0.0)


# Test load failure due to corrupt npz
def test_load_state_np_load_failure(tmp_path):
    # Arrange
    dummy_file = tmp_path / "model.npz"
    dummy_file.write_text("not a real npz file")
    obj = Dummy(str(tmp_path), 3)

    # Act
    obj.load_state(3)

    # Assert
    assert np.all(obj.moving_scores == 0.0)


# Test save creates the file
def test_save_state_creates_file(tmp_path):
    # Arrange
    obj = Dummy(str(tmp_path), 5)

    # Act
    obj.save_state()
    saved_file = os.path.join(str(tmp_path), "model.npz")

    # Assert
    assert os.path.exists(saved_file)


# Test saved contents match expectations
def test_save_state_contents(tmp_path):
    # Arrange
    obj = Dummy(str(tmp_path), 5)
    for i in range(5):
        obj.moving_scores[i] = i * 0.1
    expected = obj.moving_scores.copy()

    # Act
    obj.save_state()
    state = np.load(os.path.join(str(tmp_path), "model.npz"))

    # Assert
    assert np.allclose(state["neuron_weights"], expected)
