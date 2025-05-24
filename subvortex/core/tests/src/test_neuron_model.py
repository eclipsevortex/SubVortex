from dataclasses import dataclass, fields
from typing import Optional, get_type_hints

from subvortex.core.model.neuron import Neuron

class MockTao:
    def __init__(self, value):
        self.tao = value

class MockAxonInfo:
    def __init__(self):
        self.ip = "127.0.0.1"
        self.ip_type = 4
        self.port = 8091
        self.version = 9000000
        self.protocol = 4
        self.placeholder1 = 0
        self.placeholder2 = 0
        self.is_serving = True

class MockNeuronInfo:
    def __init__(self):
        self.uid = 1
        self.hotkey = "hk"
        self.coldkey = "ck"
        self.netuid = 7
        self.active = True
        self.stake = MockTao(10.0)
        self.total_stake = MockTao(20.0)
        self.rank = 0.5
        self.emission = 0.1
        self.incentive = 0.05
        self.consensus = 0.02
        self.trust = 0.9
        self.validator_trust = 0.8
        self.dividends = 0.0
        self.last_update = 123456
        self.validator_permit = False
        self.axon_info = MockAxonInfo()

def test_neuron_from_proto_type_consistency():
    proto = MockNeuronInfo()
    neuron = Neuron.from_proto(proto)
    expected_types = get_type_hints(Neuron)

    for field in fields(Neuron):
        name = field.name
        expected_type = expected_types[name]
        actual_value = getattr(neuron, name)

        assert isinstance(actual_value, expected_type) or actual_value is None, (
            f"❌ Field '{name}' has incorrect type. "
            f"Expected: {expected_type}, Got: {type(actual_value)}"
        )