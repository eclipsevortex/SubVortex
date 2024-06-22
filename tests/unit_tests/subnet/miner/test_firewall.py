import time
import unittest
import subprocess
import bittensor as bt
from unittest.mock import patch, MagicMock, call

from subnet.firewall.firewall_model import RuleType, AllowRule, DenyRule
from subnet.miner.firewall import Firewall
from subnet.bittensor.synapse import SubVortexSynapse
from subnet.protocol import Score

from tests.unit_tests.mocks.mock_packet import create_packet


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

    def send_packet(
        self,
        src_ip,
        dst_ip,
        src_port,
        dst_port,
        seq,
        ack,
        flags,
        firewall,
        mock_packet,
        mock_time,
        payload="",
        seconds=0,
    ):
        self.set_time(mock_time, seconds)
        packet = create_packet(
            src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload, mock_packet
        )
        firewall.packet_callback(packet)

    def send_request(
        self,
        src_ip,
        dst_ip,
        src_port,
        dst_port,
        firewall,
        mock_packet,
        mock_time,
        seconds=[],
        seq=1000,
        synapse="SubVortexSynapse",
        neuron_version=225,
        hotkey="5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja",
    ):
        for index in range(0, len(seconds) // 2):
            # Step 1: SYN (Client to Server)
            self.send_packet(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                seq=seq + (index * 2),
                ack=0,
                flags="S",
                firewall=firewall,
                mock_packet=mock_packet,
                mock_time=mock_time,
                seconds=seconds[index * 2],
            )

            # Step 4: PSH-ACK (Client to Server - Request Data)
            payload = "b'POST /{} HTTP/1.1\r\nHost: {}:{}\r\nname: {}\r\ntimeout: 5.0\r\nbt_header_axon_ip: {}\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip:{}\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: {}\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: {}\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'".format(
                synapse,
                dst_ip,
                dst_port,
                synapse,
                dst_ip,
                src_ip,
                hotkey,
                neuron_version,
            )
            self.send_packet(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                seq=seq + (index * 2) + 1,
                ack=1,
                flags="PA",
                payload=payload,
                firewall=firewall,
                mock_packet=mock_packet,
                mock_time=mock_time,
                seconds=seconds[index * 2 + 1],
            )


class TestRules(TestFirewall):
    @patch("builtins.open")
    def test_when_starting_the_firewall_should_create_the_predefined_allow_rules(
        self, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])

        # Action
        firewall.run()

        # Assert
        assert 4 == len(firewall.rules)
        assert AllowRule(dport=9944, protocol="tcp") == firewall.rules[0]
        assert AllowRule(dport=9933, protocol="tcp") == firewall.rules[1]
        assert AllowRule(dport=30333, protocol="tcp") == firewall.rules[2]
        assert AllowRule(dport=8091, protocol="tcp") == firewall.rules[3]

    @patch("builtins.open")
    def test_when_starting_the_firewall_should_create_the_predefined_rules_on_vps(
        self, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])

        # Action
        firewall.run()

        # Assert
        assert 9 == tool.create_allow_rule.call_count
        tool.create_allow_rule.assert_has_calls(
            [
                call(dport=22, protocol="tcp"),
                call(dport=443, protocol="tcp"),
                call(sport=443, protocol="tcp"),
                call(sport=80, protocol="tcp"),
                call(sport=53, protocol="udp"),
                call(dport=9944, protocol="tcp"),
                call(dport=9933, protocol="tcp"),
                call(dport=30333, protocol="tcp"),
                call(dport=8091, protocol="tcp", queue=1),
            ]
        )
        tool.create_deny_policy.assert_called_once()


class TestPackets(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_given_no_rules_when_receiving_all_packets_for_tcp_requests_should_deny_all_of_them(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=7,
        )

        # Step 9: ACK (Server to Client)

        # Step 10: FIN-ACK (Server to Client)
        server_seq += len(payload)

        # Step 11: ACK (Client to Server)
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_ack,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Deny ip",
        } == firewall.ips_blocked[0]
        assert 6 == packet_mock.drop.call_count
        assert 0 == packet_mock.accept.call_count

    @patch("builtins.open")
    @patch("time.time")
    def test_given_an_allow_rule_packet_when_receiving_all_packets_for_tcp_requests_should_accept_all_of_them(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.run()

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=7,
        )

        # Step 9: ACK (Server to Client)

        # Step 10: FIN-ACK (Server to Client)
        server_seq += len(payload)

        # Step 11: ACK (Client to Server)
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_ack,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=10,
        )

        # Assert
        assert 0 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        packet_mock.drop.assert_not_called()
        assert 6 == packet_mock.accept.call_count

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_deny_rule_packet_when_receiving_all_packets_for_tcp_requests_should_deny_all_of_them(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.run()
        firewall.rules = firewall.rules[:-1] + [DenyRule(dport=8091, protocol="tcp")]

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /SubVortexSynapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: SubVortexSynapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=7,
        )

        # Step 9: ACK (Server to Client)

        # Step 10: FIN-ACK (Server to Client)
        server_seq += len(payload)

        # Step 11: ACK (Client to Server)
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=client_ack,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Deny ip",
        } == firewall.ips_blocked[0]
        assert 6 == packet_mock.drop.call_count
        packet_mock.accept.assert_not_called()


class TestDoSAttacks(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_dos_rule_when_a_dos_attack_is_detected_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count  # Accept S/FA from first request
        assert 2 == packet_mock.drop.call_count  # Drop S/FA from second request
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DOS,
            "reason": "DoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_dos_rule_when_no_dos_attack_detected_should_allow_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1, 30, 31],
        )

        # Assert
        assert 0 == len(firewall.ips_blocked)
        assert 4 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_dos_rule_and_a_previous_request_denied_when_a_dos_attack_is_detected_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        assert 2 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DOS,
            "reason": "DoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]

        # Arrange
        packet_mock.reset_mock()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[56, 57],
        )

        assert 1 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called
        assert 2 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DOS,
            "reason": "DoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_dos_rule_and_a_previous_request_denied_when_not_dos_attack_is_detected_should_allow_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        assert 2 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DOS,
            "reason": "DoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]

        # Arrange
        packet_mock.reset_mock()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[60, 61],
        )

        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called


class TestDDoSAttacks(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_when_a_ddos_attack_is_detected_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
        )

        self.send_request(
            src_ip="192.168.0.3",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count  # Accept S/FA from first request
        assert 2 == packet_mock.drop.call_count  # Drop S/FA from second request
        assert {
            "ip": "192.168.0.3",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DDOS,
            "reason": "DDoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_when_no_ddos_attack_is_detected_should_allow_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
        )

        self.send_request(
            src_ip="192.168.0.3",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[30, 31],
        )

        # Assert
        assert 0 == len(firewall.ips_blocked)
        assert 4 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_and_a_previous_request_denied_when_a_ddos_attack_is_detected_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
        )

        self.send_request(
            src_ip="192.168.0.3",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count  # Accept S/FA from first request
        assert 2 == packet_mock.drop.call_count  # Drop S/FA from second request
        assert {
            "ip": "192.168.0.3",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DDOS,
            "reason": "DDoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]

        # Arrange
        packet_mock.reset_mock()

        # Action
        self.send_request(
            src_ip="192.168.0.4",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[56, 57],
        )

        assert 2 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called
        assert 2 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.3",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DDOS,
            "reason": "DDoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]
        assert {
            "ip": "192.168.0.4",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DDOS,
            "reason": "DDoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[1]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_and_a_previous_request_denied_when_no_ddos_attack_is_detected_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
        )

        self.send_request(
            src_ip="192.168.0.3",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count  # Accept S/FA from first request
        assert 2 == packet_mock.drop.call_count  # Drop S/FA from second request
        assert {
            "ip": "192.168.0.3",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DDOS,
            "reason": "DDoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]

        # Arrange
        packet_mock.reset_mock()

        # Action
        self.send_request(
            src_ip="192.168.0.4",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[60, 61],
        )

        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called
        assert {
            "ip": "192.168.0.3",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DETECT_DDOS,
            "reason": "DDoS attack detected: 2 requests in 30 seconds",
        } == firewall.ips_blocked[0]


class TestMiner(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_deny_rule_when_packet_contains_a_blacklisted_hotkey_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"SubVortexSynapse": SubVortexSynapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
            blacklist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()
        firewall.rules = firewall.rules[:-1] + [DenyRule(dport=8091, protocol="tcp")]

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called()
        assert 2 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Deny ip",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_deny_rule_when_packet_contains_unknown_synapse_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"SubVortexSynapse": SubVortexSynapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
        )
        firewall.run()
        firewall.rules = firewall.rules[:-1] + [DenyRule(dport=8091, protocol="tcp")]

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
            synapse="QnATask",
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called()
        assert 2 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Deny ip",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_deny_rule_when_packet_contains_outdated_version_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"SubVortexSynapse": SubVortexSynapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
        )
        firewall.run()
        firewall.rules = firewall.rules[:-1] + [DenyRule(dport=8091, protocol="tcp")]

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
            neuron_version=224,
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called()
        assert 2 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Deny ip",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_an_allow_rule_when_packet_contains_a_blacklisted_hotkey_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"SubVortexSynapse": SubVortexSynapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
            blacklist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 1 == packet_mock.accept.call_count
        assert 1 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_an_allow_rule_when_packet_contains_unknown_synapse_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"SubVortexSynapse": SubVortexSynapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
            synapse="QnATask",
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 1 == packet_mock.accept.call_count
        assert 1 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Synapse name 'QnATask' not found, available ['SubVortexSynapse', 'Score']",
        } == firewall.ips_blocked[0]

    @patch("builtins.open")
    @patch("time.time")
    def test_given_an_allow_rule_when_packet_contains_outdated_version_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"SubVortexSynapse": SubVortexSynapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
            neuron_version=224,
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 1 == packet_mock.accept.call_count
        assert 1 == packet_mock.drop.call_count
        assert {
            "ip": "192.168.0.1",
            "port": 8091,
            "protocol": "tcp",
            "type": RuleType.DENY,
            "reason": "Neuron version 224 is outdated; version 225 is required.",
        } == firewall.ips_blocked[0]
