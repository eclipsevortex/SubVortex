import pytest

from neurons.validator import Validator

@pytest.fixture(scope="session", autouse=True)
def validator():
    config = Validator.config()
    config.mock = True
    config.wandb.off = True
    config.neuron.dont_save_events = True
    validator = Validator(config)
    yield validator