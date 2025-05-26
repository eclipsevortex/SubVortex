import pytest
from dataclasses import fields
from typing import get_type_hints

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


def build_base_neuron() -> Neuron:
    return Neuron(
        uid=1,
        hotkey="hotkey",
        coldkey="coldkey",
        netuid=42,
        active=True,
        stake=10.0,
        total_stake=20.0,
        rank=0.1,
        emission=0.01,
        incentive=0.02,
        consensus=0.03,
        trust=0.9,
        validator_trust=0.8,
        dividends=0.0,
        last_update=123456,
        validator_permit=True,
        ip="127.0.0.1",
        ip_type=4,
        port=8000,
        version=1,
        protocol=4,
        placeholder1=0,
        placeholder2=0,
        is_serving=True,
        country="US",
    )


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


def test_to_dict_country_none_becomes_empty_string():
    neuron = Neuron(uid=1, country=None)
    data = neuron.to_dict()
    assert (
        data["country"] == ""
    ), f"❌ Expected country='' in dict, got {data['country']}"


def test_from_dict_country_empty_string_or_none_becomes_none():
    # Case 1: country is None in dict
    data_none = {
        "uid": 1,
        "hotkey": "hk",
        "coldkey": "ck",
        "netuid": 7,
        "active": 1,
        "stake": 10.0,
        "total_stake": 20.0,
        "rank": 0.5,
        "emission": 0.1,
        "incentive": 0.05,
        "consensus": 0.02,
        "trust": 0.9,
        "validator_trust": 0.8,
        "dividends": 0.0,
        "last_update": 123456,
        "validator_permit": 0,
        "ip": "127.0.0.1",
        "ip_type": 4,
        "port": 8091,
        "version": 9000000,
        "protocol": 4,
        "placeholder1": 0,
        "placeholder2": 0,
        "is_serving": 1,
        "country": None,
    }
    neuron_none = Neuron.from_dict(data_none)
    assert (
        neuron_none.country is None
    ), f"❌ Expected country='none' for None input, got {neuron_none.country}"

    # Case 2: country is an empty string in dict
    data_empty = dict(data_none)
    data_empty["country"] = ""
    neuron_empty = Neuron.from_dict(data_empty)
    assert (
        neuron_empty.country is None
    ), f"❌ Expected country='none' for empty string input, got {neuron_empty.country}"

    # Case 3: country is a space string in dict
    data_empty = dict(data_none)
    data_empty["country"] = "  "
    neuron_empty = Neuron.from_dict(data_empty)
    assert (
        neuron_empty.country is None
    ), f"❌ Expected country='none' for empty string input, got {neuron_empty.country}"


@pytest.mark.parametrize("field", [f.name for f in fields(Neuron)])
def test_neuron_eq_differs_on_each_field(field):
    base = build_base_neuron()
    modified = build_base_neuron()

    original_value = getattr(base, field)

    # Change the field in a way that's guaranteed to differ
    if isinstance(original_value, bool):
        setattr(modified, field, not original_value)
    elif isinstance(original_value, int):
        setattr(modified, field, original_value + 1)
    elif isinstance(original_value, float):
        setattr(modified, field, original_value + 0.1)
    elif isinstance(original_value, str):
        setattr(modified, field, original_value + "_diff")
    elif original_value is None:
        setattr(modified, field, "not_none")
    else:
        raise TypeError(f"Unhandled type for field '{field}'")

    assert base != modified, f"❌ Neuron instances should differ when '{field}' changes"


def test_neuron_eq_all_fields_equal():
    n1 = build_base_neuron()
    n2 = build_base_neuron()
    assert n1 == n2, "❌ Neuron instances with identical fields should be equal"
