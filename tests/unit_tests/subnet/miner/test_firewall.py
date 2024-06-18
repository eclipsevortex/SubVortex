import time
import unittest
import subprocess
import bittensor as bt
from scapy.all import IP, TCP, Raw, Packet
from unittest.mock import patch, MagicMock, call

from subnet.firewall.firewall_model import RuleType
from subnet.miner.firewall import Firewall


DEFAULT_PING_SYNAPSE = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 158.220.82.181\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"


def is_sublist(sublist, main_list):
    sublist_len = len(sublist)
    main_list_len = len(main_list)

    for i in range(main_list_len - sublist_len + 1):
        if main_list[i : i + sublist_len] == sublist:
            return True
    return False


def mock_check_rule(
    mock_run, returncode, cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
):
    if is_sublist(["sudo", "iptables", "-C", "INPUT"], cmd):
        return subprocess.CompletedProcess(
            args=cmd, returncode=returncode, stdout=stdout, stderr=stderr
        )
    else:
        return mock_run


class TestFirewall(unittest.TestCase):
    def setUp(self):
        bt.logging.on()

    def tearDown(self):
        bt.logging.off()

    def assert_blocked(self, firewall, ip, port, protocol, rule_type):
        block = next(
            (
                x
                for x in firewall.ips_blocked
                if x.get("ip") == ip
                and x.get("port") == port
                and x.get("protocol") == protocol
                and x.get("type") == rule_type
            ),
            None,
        )
        assert block is not None

    def set_time(self, mock_time, second=0):
        specific_time = time.struct_time((2024, 5, 28, 12, 0, second, 0, 0, -1))
        mock_time.return_value = time.mktime(specific_time)


class TestNoRules(TestFirewall):
    @patch("time.time")
    def test_given_a_packet_when_no_rules_should_deny_the_packet(self, mock_time):
        # Arrange
        tool = MagicMock()

        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=tool, interface="eth0", rules=[])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.create_allow_rule.assert_not_called()


class TestAllowRules(TestFirewall):
    @patch("builtins.open")
    @patch("subnet.miner.firewall.sniff")
    def test_when_a_port_allow_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"port": 22, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_called_once_with(ip=None, port=22, protocol="tcp")
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("builtins.open")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_allow_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "type": "allow"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_called_once_with(
            ip="192.168.10.1", port=None, protocol=None
        )
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("builtins.open")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_and_port_allow_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "port": 22, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_called_once_with(
            ip="192.168.10.1", port=22, protocol="tcp"
        )
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()


class TestDenyRules(TestFirewall):
    @patch("builtins.open")
    @patch("subnet.miner.firewall.sniff")
    def test_when_a_port_deny_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"port": 22, "protocol": "tcp", "type": "deny"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(ip=None, port=22, protocol="tcp")
        tool.remove_rule.assert_not_called()

    @patch("builtins.open")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_deny_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "type": "deny"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.10.1", port=None, protocol=None
        )
        tool.remove_rule.assert_not_called()

    @patch("builtins.open")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_and_port_deny_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "port": 22, "protocol": "tcp", "type": "deny"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.10.1", port=22, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()


class TestPortRules(TestFirewall):
    @patch("time.time")
    def test_given_no_port_rules_when_a_packet_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        firewall = Firewall(tool=tool, interface="eth0")
        packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_a_tcp_port_allow_rule_when_a_packet_on_that_port_is_received_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [{"port": 8091, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_a_tcp_port_allow_rule_when_a_packet_on_different_port_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [{"port": 8091, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet = (
            TCP(dport=8092) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8092,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8092, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()


class TestIpRules(TestFirewall):
    @patch("time.time")
    def test_given_no_ip_rules_when_a_packet_on_that_ip_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        firewall = Firewall(tool=tool, interface="eth0")
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_a_ip_allow_rule_when_a_packet_on_different_ip_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [{"ip": "192.168.0.1", "type": "allow"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.2", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_a_ip_allow_rule_when_a_packet_on_that_ip_is_received_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [{"ip": "192.168.0.1", "type": "allow"}]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()


class TestIpAndPortRules(TestFirewall):
    @patch("time.time")
    def test_given_no_ip_an_port_rules_when_a_packet_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        firewall = Firewall(tool=tool, interface="eth0")
        packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_that_port_but_different_ip_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet = (
            TCP(dport=8091) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.2", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_that_ip_but_different_port_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet = (
            TCP(dport=8092) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8092,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8092, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_that_ip_and_port_is_received_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_different_ip_and_port_is_received_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)
        packet = (
            TCP(dport=8092) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.2",
            port=8092,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.2", port=8092, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()


class TestDoSAttacks(TestFirewall):
    @patch("time.time")
    def test_given_an_ip_dos_rule_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_dos_rule_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp", allow=False
        )

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp", allow=False
        )


class TestDDoSAttacks(TestFirewall):
    @patch("time.time")
    def test_given_an_ip_ddos_rule_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_dos_rule_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        # Action
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp", allow=False
        )

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp", allow=False
        )

    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_a_ddos_attack_is_detected_on_a_packet_from_different_ip_should_deny_the_packet_and_still_block_packets_on_initial_ip(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        rules = [
            {
                "port": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(tool=tool, interface="eth0", rules=rules)

        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

        # Arrange
        tool.reset_mock()
        packet: Packet = (
            TCP(dport=8091) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)
        )

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 2 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        self.assert_blocked(
            firewall,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DETECT_DDOS,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.2", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()


class TestCheckSpecificationsRules(TestFirewall):
    @patch("time.time")
    def test_when_packet_contains_unknown_synapse_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        specifications = {
            "neuron_version": 225,
            "synapses": ["subvortexsynapse", "score"],
        }

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_when_packet_contains_outdated_version_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        payload = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 224\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        specifications = {
            "neuron_version": 225,
            "synapses": ["subvortexsynapse", "score"],
        }

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_when_packet_contains_required_version_and_available_synapse_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()
        payload = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        specifications = {
            "neuron_version": 225,
            "synapses": ["subvortexsynapse", "score"],
        }

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()


class TestWhitelistRules(TestFirewall):
    @patch("time.time")
    def test_given_a_packet_when_source_is_not_whitelisted_should_deny_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()

        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Jb"]
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_a_packet_when_source_is_whitelisted_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()

        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()


class TestBlacklistRules(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_packet_when_source_is_blacklisted_should_deny_the_packet(
        self, mock_time, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            blacklist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_packet_when_source_is_not_blacklisted_but_not_whitelisted_should_deny_the_packet(
        self, mock_time, mock_open
    ):
        # Arrange
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            blacklist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Jb"]
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        self.assert_blocked(
            firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            rule_type=RuleType.DENY,
        )
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_called_once_with(
            ip="192.168.0.1", port=8091, protocol="tcp"
        )
        tool.remove_rule.assert_not_called()

    @patch("time.time")
    def test_given_a_packet_when_source_is_not_blacklisted_and_whitelisted_should_allow_the_packet(
        self, mock_time
    ):
        # Arrange
        tool = MagicMock()

        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=tool, interface="eth0")
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
            blacklist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Jb"],
        )

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        tool.create_allow_rule.assert_not_called()
        tool.create_deny_rule.assert_not_called()
        tool.remove_rule.assert_not_called()
