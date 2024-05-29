import time
import unittest
import subprocess
import bittensor as bt
from functools import partial
from scapy.all import IP, TCP, Packet
from unittest.mock import patch, MagicMock

from subnet.miner.firewall import Firewall
from subnet.miner.firewall_models import RuleType


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

    def assert_unblocked(self, firewall, ip, port, protocol, rule_type, process_run):
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
        assert process_run.call_count == 2
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
        firewall = Firewall("eth0", rules=rules)

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
        firewall = Firewall("eth0", rules=rules)

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
        firewall = Firewall("eth0", rules=rules)

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
        firewall = Firewall("eth0", rules=rules)

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
        firewall = Firewall("eth0", rules=rules)

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
        firewall = Firewall("eth0", rules=rules)

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
        firewall = Firewall("eth0")
        packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)
        packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)
        packet = TCP(dport=8092) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0")
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.2")

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
        firewall = Firewall("eth0", rules=rules)
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0")
        packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)
        packet = TCP(dport=8091) / IP(src="192.168.0.2")

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
        firewall = Firewall("eth0", rules=rules)
        packet = TCP(dport=8092) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)
        packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)
        packet = TCP(dport=8092) / IP(src="192.168.0.2")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        # Action
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        firewall = Firewall("eth0", rules=rules)

        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.1")

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
        packet: Packet = TCP(dport=8091) / IP(src="192.168.0.2")

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
