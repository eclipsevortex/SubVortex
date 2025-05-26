import pytest

from subvortex.core.utils import is_valid_ipv4


@pytest.mark.parametrize(
    "ip",
    [
        "192.168.1.1",
        "8.8.8.8",
        "127.0.0.1",
        "0.0.0.0",
        "255.255.255.255",
    ],
)
def test_valid_ipv4_addresses(ip):
    assert is_valid_ipv4(ip), f"❌ {ip} should be recognized as valid IPv4"


@pytest.mark.parametrize(
    "ip",
    [
        "::1",
        "2001:db8::1",
        "fe80::",
        "::ffff:192.0.2.128",  # IPv4-mapped IPv6
        "abcd::1234",
    ],
)
def test_valid_ipv6_addresses(ip):
    assert not is_valid_ipv4(ip), f"❌ {ip} should NOT be recognized as IPv4"


@pytest.mark.parametrize(
    "ip",
    [
        "",
        "   ",
        "not.an.ip",
        "256.256.256.256",
        "192.168.1.999",
        "1234.123.123.123",
        "....",
        "::",
        "::360:c054:1f9b",
    ],
)
def test_invalid_ips(ip):
    assert not is_valid_ipv4(ip), f"❌ {ip} should NOT be recognized as valid IPv4"


def test_is_valid_ipv4_type_safety():
    # Non-string inputs
    assert not is_valid_ipv4(None)
    assert not is_valid_ipv4(1234)
    assert not is_valid_ipv4(["192.168.1.1"])
