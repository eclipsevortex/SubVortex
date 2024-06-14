import time
import unittest
import subprocess
import bittensor as bt
from functools import partial
from scapy.all import IP, TCP, Raw, Packet
from unittest.mock import patch, MagicMock

from subnet.firewall.firewall_factory import create_firewall_tool
from subnet.miner.firewall import Firewall
from subnet.miner.firewall_models import RuleType


DEFAULT_PING_SYNAPSE = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 158.220.82.181\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
FIREWALL_TOOL = create_firewall_tool("iptables")


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

    def assert_not_called_with(self, mock, *args, **kwargs):
        """
        Custom assertion to check that the mock was not called with the specified arguments.
        """
        if any(
            call == unittest.mock.call(*args, **kwargs) for call in mock.call_args_list
        ):
            raise AssertionError(
                f"Mock was called with arguments {args} and keyword arguments {kwargs}"
            )

    def assert_blocked(
        self, firewall, ip, port, protocol, rule_type, process_run, index=0, count=2
    ):
        block = next(
            (
                x
                for x in firewall.ips_blocked
                if x.get("ip") == ip
                and x.get("port") == port
                and x.get("type") == rule_type
            ),
            None,
        )
        assert block is not None
        assert process_run.call_count == count
        assert process_run.call_args_list[index + 0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-s",
                ip,
                "-p",
                protocol,
                "--dport",
                str(port),
                "-j",
                "DROP",
            ],
        )
        assert process_run.call_args_list[index + 1][0] == (
            [
                "sudo",
                "iptables",
                "-I",
                "INPUT",
                "-s",
                ip,
                "-p",
                protocol,
                "--dport",
                str(port),
                "-j",
                "DROP",
            ],
        )

    def assert_unblocked(
        self, firewall, ip, port, protocol, rule_type, process_run, count=2
    ):
        block = next(
            (
                x
                for x in firewall.ips_blocked
                if x.get("ip") == ip
                and x.get("port") == port
                and x.get("type") == rule_type
            ),
            None,
        )
        assert block is None
        assert process_run.call_count == count
        assert process_run.call_args_list[0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-s",
                ip,
                "-p",
                protocol,
                "--dport",
                str(port),
                "-j",
                "DROP",
            ],
        )
        assert process_run.call_args_list[1][0] == (
            [
                "sudo",
                "iptables",
                "-D",
                "INPUT",
                "-s",
                ip,
                "-p",
                protocol,
                "--dport",
                str(port),
                "-j",
                "DROP",
            ],
        )

    def set_time(self, mock_time, second=0):
        specific_time = time.struct_time((2024, 5, 28, 12, 0, second, 0, 0, -1))
        mock_time.return_value = time.mktime(specific_time)


class TestAllowRules(TestFirewall):
    @patch("codecs.open")
    @patch("subprocess.run")
    @patch("subnet.miner.firewall.sniff")
    def test_when_a_port_allow_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_run, mock_open
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = []

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"port": 22, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "ACCEPT",
            ],
        )
        assert mock_run.call_args_list[1][0] == (
            [
                "sudo",
                "iptables",
                "-I",
                "INPUT",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "ACCEPT",
            ],
        )

    @patch("codecs.open")
    @patch("subprocess.run")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_allow_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_run, mock_open
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = []

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "type": "allow"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-j",
                "ACCEPT",
            ],
        )
        assert mock_run.call_args_list[1][0] == (
            [
                "sudo",
                "iptables",
                "-I",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-j",
                "ACCEPT",
            ],
        )

    @patch("codecs.open")
    @patch("subprocess.run")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_and_port_allow_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_run, mock_open
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = []

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "port": 22, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "ACCEPT",
            ],
        )
        assert mock_run.call_args_list[1][0] == (
            [
                "sudo",
                "iptables",
                "-I",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "ACCEPT",
            ],
        )


class TestDenyRules(TestFirewall):
    @patch("codecs.open")
    @patch("subprocess.run")
    @patch("subnet.miner.firewall.sniff")
    def test_when_a_port_deny_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_run, mock_open
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = []

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"port": 22, "protocol": "tcp", "type": "deny"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "DROP",
            ],
        )
        assert mock_run.call_args_list[1][0] == (
            [
                "sudo",
                "iptables",
                "-I",
                "INPUT",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "DROP",
            ],
        )

    @patch("codecs.open")
    @patch("subprocess.run")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_deny_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_run, mock_open
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = []

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "type": "deny"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-j",
                "DROP",
            ],
        )
        assert mock_run.call_args_list[1][0] == (
            [
                "sudo",
                "iptables",
                "-I",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-j",
                "DROP",
            ],
        )

    @patch("codecs.open")
    @patch("subprocess.run")
    @patch("subnet.miner.firewall.sniff")
    def test_when_an_ip_and_port_deny_rule_is_provided_should_update_iptables_accordingly(
        self, mock_sniff, mock_run, mock_open
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = []

        mock_sniff.side_effect = lambda *args, **kwargs: [MagicMock()]

        rules = [{"ip": "192.168.10.1", "port": 22, "protocol": "tcp", "type": "deny"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        firewall.run()

        # Assets
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0] == (
            [
                "sudo",
                "iptables",
                "-C",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "DROP",
            ],
        )
        assert mock_run.call_args_list[1][0] == (
            [
                "sudo",
                "iptables",
                "-I",
                "INPUT",
                "-s",
                "192.168.10.1",
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "DROP",
            ],
        )


class TestPortRules(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_given_no_port_rules_when_a_packet_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_tcp_port_allow_rule_when_a_packet_on_that_port_is_received_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [{"port": 8091, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_tcp_port_allow_rule_when_a_packet_on_different_port_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [{"port": 8091, "protocol": "tcp", "type": "allow"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet = TCP(dport=8092) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8092, "tcp", RuleType.DENY, mock_run
        )


class TestIpRules(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_given_no_ip_rules_when_a_packet_on_that_ip_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_ip_allow_rule_when_a_packet_on_different_ip_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [{"ip": "192.168.0.1", "type": "allow"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.2", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_ip_allow_rule_when_a_packet_on_that_ip_is_received_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [{"ip": "192.168.0.1", "type": "allow"}]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()


class TestIpAndPortRules(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_given_no_ip_an_port_rules_when_a_packet_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_that_port_but_different_ip_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet = TCP(dport=8091) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.2", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_that_ip_but_different_port_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet = TCP(dport=8092) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8092, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_that_ip_and_port_is_received_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_rule_when_a_packet_on_different_ip_and_port_is_received_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        rules = [
            {"ip": "192.168.0.1", "port": 8091, "protocol": "tcp", "type": "allow"}
        ]
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)
        packet = TCP(dport=8092) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.2", 8092, "tcp", RuleType.DENY, mock_run
        )


class TestDoSAttacks(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_dos_rule_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_dos_rule_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()
        mock_run.side_effect = partial(mock_check_rule, mock_run, 0)

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        self.assert_unblocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )

        # assert 0 == len(firewall.ips_blocked)
        # mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_a_dos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_no_dos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()
        mock_run.side_effect = partial(mock_check_rule, mock_run, 0)

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        self.assert_unblocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DOS, mock_run
        )


class TestDDoSAttacks(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_ddos_rule_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_dos_rule_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 30)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_dos_rule_blocking_previous_packet_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()
        mock_run.side_effect = partial(mock_check_rule, mock_run, 0)

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        self.assert_unblocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_a_ddos_attack_is_detected_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        assert 1 == len(firewall.ips_blocked)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_no_ddos_attack_detected_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

        # Arrange
        mock_run.reset_mock()
        mock_run.side_effect = partial(mock_check_rule, mock_run, 0)

        # Action
        self.set_time(mock_time, 60)
        firewall.packet_callback(packet)

        # Assets
        self.assert_unblocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_an_ip_and_tcp_port_dos_rule_blocking_previous_packet_when_a_ddos_attack_is_detected_on_a_packet_from_different_ip_should_deny_the_packet_and_still_block_packets_on_initial_ip(
        self, mock_time, mock_run
    ):
        # Arrange
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
        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time)
        firewall.packet_callback(packet)

        self.set_time(mock_time, 29)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DETECT_DDOS, mock_run
        )

        # Arrange
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.2") / Raw(load=DEFAULT_PING_SYNAPSE)

        # Action
        self.set_time(mock_time, 58)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall,
            "192.168.0.1",
            8091,
            "tcp",
            RuleType.DETECT_DDOS,
            mock_run,
            count=4,
        )
        self.assert_blocked(
            firewall,
            "192.168.0.2",
            8091,
            "tcp",
            RuleType.DETECT_DDOS,
            mock_run,
            index=2,
            count=4,
        )


class TestCheckSpecificationsRules(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_when_packet_contains_unknown_synapse_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        specifications = { "neuron_version": 225, "synapses": ['subvortexsynapse', 'score'] }

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_specifications(specifications)
        firewall.update_whitelist(["192.168.0.1"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.SPECIFICATION, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_when_packet_contains_outdated_version_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 224\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        specifications = { "neuron_version": 225, "synapses": ['subvortexsynapse', 'score'] }

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_specifications(specifications)
        firewall.update_whitelist(["192.168.0.1"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.SPECIFICATION, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_when_packet_contains_required_version_and_available_synapse_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        specifications = {
            "neuron_version": 225,
            "synapses": ["subvortexsynapse", "score"],
        }

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_specifications(specifications)
        firewall.update_whitelist(["192.168.0.1"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()


class TestWhitelistRules(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_packet_when_source_is_not_whitelisted_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_whitelist(["192.168.0.2"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_packet_when_source_is_whitelisted_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_whitelist(["192.168.0.1"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()


class TestBlacklistRules(TestFirewall):
    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_packet_when_source_is_blacklisted_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_blacklist(["192.168.0.1"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_packet_when_source_is_not_blacklisted_but_not_whitelisted_should_deny_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_blacklist(["192.168.0.2"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        self.assert_blocked(
            firewall, "192.168.0.1", 8091, "tcp", RuleType.DENY, mock_run
        )

    @patch("subprocess.run")
    @patch("time.time")
    def test_given_a_packet_when_source_is_not_blacklisted_and_whitelisted_should_allow_the_packet(
        self, mock_time, mock_run
    ):
        # Arrange
        payload = "b'POST /QnATask HTTP/1.1\r\nHost: 167.86.79.86:8091\r\nname: QnATask\r\ntimeout: 5.0\r\nbt_header_axon_ip: 167.86.79.86\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"

        firewall = Firewall(tool=FIREWALL_TOOL, interface="eth0")
        firewall.update_blacklist(["192.168.0.2"])
        firewall.update_whitelist(["192.168.0.1"])

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1") / Raw(load=payload)

        self.set_time(mock_time)
        firewall.packet_callback(packet)

        # Assets
        assert 0 == len(firewall.ips_blocked)
        mock_run.assert_not_called()