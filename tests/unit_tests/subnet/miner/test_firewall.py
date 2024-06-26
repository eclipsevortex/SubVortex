import time
import unittest
import bittensor as bt
from unittest.mock import patch, MagicMock

from subnet.firewall.firewall_model import RuleType
from subnet.miner.firewall import Firewall
from subnet.bittensor.synapse import Synapse
from subnet.protocol import Score

from tests.unit_tests.mocks.mock_packet import create_packet


def is_sublist(sublist, main_list):
    sublist_len = len(sublist)
    main_list_len = len(main_list)

    for i in range(main_list_len - sublist_len + 1):
        if main_list[i : i + sublist_len] == sublist:
            return True
    return False


def get_time(second):
    specific_time = time.struct_time((2024, 5, 28, 12, 0, second, 0, 0, -1))
    return time.mktime(specific_time)


class TestFirewall(unittest.TestCase):
    def setUp(self):
        bt.logging.on()

    def tearDown(self):
        bt.logging.off()

    def assert_blocked(self, firewall, ip, port, protocol, type, reason):
        block = next(
            (
                x
                for x in firewall.ips_blocked
                if x.get("ip") == ip
                and x.get("port") == port
                and x.get("protocol") == protocol
                and x.get("type") == type
                and x.get("reason") == reason
            ),
            None,
        )
        assert block is not None

    def set_time(self, mock_time, second=0):
        mock_time.return_value = get_time(second)

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
        synapse="Synapse",
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


class TestPackets(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_given_no_rules_when_receiving_all_packets_for_tcp_requests_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
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
        assert 1 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == packet_mock.accept.call_count
        assert 4 == packet_mock.drop.call_count

    @patch("builtins.open")
    @patch("time.time")
    def test_given_an_allow_rule_when_receiving_all_packets_for_tcp_requests_should_allow_all_of_them(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "allow",
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
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
    def test_given_a_deny_rule_when_receiving_all_packets_for_tcp_requests_should_deny_all_of_them(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "deny",
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
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
        assert 1 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Deny ip",
        )
        assert 6 == packet_mock.drop.call_count
        packet_mock.accept.assert_not_called()

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_dos_rule_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
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
        assert 1 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == packet_mock.accept.call_count
        assert 4 == packet_mock.drop.call_count

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_dos_rule_and_hotkey_whitelisted_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_of_them(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.whitelist_hotkeys = [
            "5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"
        ]
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
    def test_given_a_dos_rule_when_receiving_all_packets_for_tcp_requests_triggering_an_alert_should_deny_all_of_them(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-dos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Simulate an old requests
        mock_time.return_value = get_time(0)
        firewall.packet_timestamps["192.168.0.1"][8091]["tcp"] = [
            mock_time.return_value
        ]
        seconds = 28

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
            seconds=seconds,
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
            seconds=seconds + 2,
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
            seconds=seconds + 3,
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
            seconds=seconds + 6,
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
            seconds=seconds + 10,
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        assert 0 == packet_mock.accept.call_count
        assert 6 == packet_mock.drop.call_count

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
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
        assert 1 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == packet_mock.accept.call_count
        assert 4 == packet_mock.drop.call_count

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_and_hotkey_whitelisted_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_of_them(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.whitelist_hotkeys = [
            "5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"
        ]
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
    def test_given_a_ddos_rule_when_receiving_all_packets_for_tcp_requests_triggering_an_alert_should_deny_all_of_them(
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

        rules = [
            {
                "dport": 8091,
                "protocol": "tcp",
                "type": "detect-ddos",
                "configuration": {
                    "time_window": 30,
                    "packet_threshold": 1,
                },
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.run()

        # Simulate an old requests
        mock_time.return_value = get_time(0)
        firewall.packet_timestamps["192.168.0.1"][8091]["tcp"] = [
            get_time(0),
            get_time(1),
        ]
        firewall.packet_timestamps["192.168.0.2"][8091]["tcp"] = [get_time(2)]
        firewall.packet_timestamps["192.168.0.3"][8091]["tcp"] = [get_time(3)]
        firewall.packet_timestamps["192.168.0.4"][8091]["tcp"] = [get_time(4)]
        seconds = 28

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
            seconds=seconds,
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
            seconds=seconds + 2,
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
            seconds=seconds + 3,
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
            seconds=seconds + 6,
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
            seconds=seconds + 10,
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 3 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DETECT_DDOS,
            reason="DDoS attack detected: 3 requests in 30 seconds",
        )
        assert 0 == packet_mock.accept.call_count
        assert 6 == packet_mock.drop.call_count

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_whitelist_hotkey_when_receiving_all_packets_for_tcp_requests_should_allow_all_of_them(
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
        firewall.whitelist_hotkeys = [
            "5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"
        ]
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
    def test_given_a_blacklist_hotkey_when_receiving_all_packets_for_tcp_requests_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
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
        assert 1 == len(firewall.ips_blocked)
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == packet_mock.accept.call_count
        assert 4 == packet_mock.drop.call_count


class TestDoSRule(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_only_requests_within_time_window_are_kept(self, mock_time, mock_open):
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
                    "packet_threshold": 4,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[28, 29],
        )

        # Assert
        assert 2 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[31, 32],
        )

        # Assert
        assert 2 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])

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
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count  # Accept S/FA from first request
        assert 2 == packet_mock.drop.call_count  # Drop S/FA from second request
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )

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
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        assert 2 == packet_mock.drop.call_count
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )

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
            seq=2000,
            seconds=[56, 57],
        )

        assert 1 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called
        assert 2 == packet_mock.drop.call_count
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )

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
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        assert 2 == packet_mock.drop.call_count
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )

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
            seq=2000,
            seconds=[60, 61],
        )

        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called


class TestDDoSRule(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_only_requests_within_time_window_are_kept(self, mock_time, mock_open):
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
                    "packet_threshold": 4,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall.packet_timestamps.keys())
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])

        # Action
        self.send_request(
            src_ip="192.168.0.2",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[28, 29],
        )

        # Assert
        assert 2 == len(firewall.packet_timestamps.keys())
        assert 1 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        assert 1 == len(firewall.packet_timestamps["192.168.0.2"][8091]["tcp"])

        # Action
        self.send_request(
            src_ip="192.168.0.3",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[31, 32],
        )

        # Assert
        assert 3 == len(firewall.packet_timestamps.keys())
        assert 0 == len(firewall.packet_timestamps["192.168.0.1"][8091]["tcp"])
        assert 1 == len(firewall.packet_timestamps["192.168.0.2"][8091]["tcp"])
        assert 1 == len(firewall.packet_timestamps["192.168.0.3"][8091]["tcp"])

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_when_receive_less_requests_than_the_benchmark_within_the_time_window_should_allow_the_request(
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
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
    def test_given_a_ddos_rule_when_receive_more_requests_than_the_benchmark_within_the_time_window_but_does_not_trigger_ddos_attack_should_allow_the_request(
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
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
        assert 0 == len(firewall.ips_blocked)
        assert 4 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_ddos_rule_when_receive_more_requests_than_the_benchmark_within_the_time_window_and_does_trigger_ddos_attack_should_deny_the_request(
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
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
        )
        firewall.run()

        vps = [2, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        for j, (request_count) in enumerate(vps):
            ip = "192.168.0.{}".format(j + 1)
            for _ in range(0, request_count):
                firewall.packet_timestamps[ip][8091]["tcp"].append(get_time(j))

        # Action
        seconds = len(vps)
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            mock_packet=packet_mock,
            mock_time=mock_time,
            seconds=[seconds, +1],
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called
        assert 2 == packet_mock.drop.call_count
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DETECT_DDOS,
            reason="DDoS attack detected: 3 requests in 30 seconds",
        )

    @patch("builtins.open")
    @patch("time.time")
    def test_check_ddos_attacks(self, mock_time, mock_open):
        test_cases = [
            (
                [3, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [3, 2, 3, 1, 1, 1, 1, 1, 1, 1],
                [
                    "1000000000",
                    "0000000000",
                    "0010000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
                [
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [5, 4, 4, 4, 4, 4, 4, 4, 4, 4],
                [
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [10, 4, 4, 4, 4, 4, 4, 4, 4, 4],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [10, 4, 4, 6, 4, 5, 8, 4, 4, 4],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [5, 4, 4, 5, 4, 5, 5, 4, 4, 5],
                [
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [10, 4, 4, 6, 4, 5, 12, 4, 4, 4],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000001000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [50, 4, 4, 6, 4, 5, 8, 4, 4, 4],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [20, 4, 4, 25, 4, 5, 18, 4, 4, 15],
                [
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0001000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [12, 10, 11, 13, 12, 10, 11, 12, 11, 13],
                [
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [15, 4, 4, 6, 4, 5, 8, 4, 4, 4],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [40, 4, 4, 6, 4, 5, 8, 4, 4, 4],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [10, 5, 4, 7, 6, 5, 8, 6, 4, 5],
                [
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [45, 4, 4, 40, 4, 5, 8, 4, 4, 4],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0001000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
            (
                [30, 4, 10, 5, 4, 25, 8, 4, 4, 12],
                [
                    "1000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000010000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                    "0000000000",
                ],
            ),
        ]

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
                    "time_window": 300,
                    "packet_threshold": 1,
                },
            },
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
        )
        firewall.run()

        ip_template = "192.168.0.{}"
        test_case_num = 0
        for vps, expected in test_cases:
            with self.subTest(test_case_num=test_case_num, vps=vps, expected=expected):
                test_case_num += 1
                for i, (expect) in enumerate(expected):
                    seconds = 0

                    # Loop accross all the vps
                    src_ip = ip_template.format(i + 1)

                    # Arrange
                    firewall.packet_timestamps.clear()
                    firewall.ips_blocked.clear()
                    firewall.requests.clear()

                    for j, (request_count) in enumerate(vps):
                        ip = ip_template.format(j + 1)
                        for _ in range(0, request_count):
                            firewall.packet_timestamps[ip][8091]["tcp"].append(
                                get_time(seconds)
                            )
                            seconds += 1

                    firewall.packet_timestamps[src_ip][8091]["tcp"] = (
                        firewall.packet_timestamps[src_ip][8091]["tcp"][:-1]
                    )

                    # Action
                    seconds = seconds if seconds % 2 == 0 else seconds + 1
                    self.send_request(
                        src_ip=src_ip,
                        dst_ip="192.168.1.1",
                        src_port=7091,
                        dst_port=8091,
                        firewall=firewall,
                        mock_packet=packet_mock,
                        mock_time=mock_time,
                        seconds=[seconds, seconds + 1],
                    )

                    # Assert
                    for j, digit in enumerate(expect):
                        ip = ip_template.format(j + 1)
                        ip_blocked = firewall.is_blocked(ip, 8091, "tcp")
                        count = len(firewall.packet_timestamps[ip][8091]["tcp"])

                        expected_ddos = digit == "1"
                        assert expected_ddos == ip_blocked
                        assert vps[j] == count


class TestBlackListRule(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_when_packet_contains_a_blacklisted_hotkey_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
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
        )

        # Assert
        assert 1 == len(firewall.ips_blocked)
        assert 1 == packet_mock.accept.call_count
        assert 1 == packet_mock.drop.call_count
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )

    @patch("builtins.open")
    @patch("time.time")
    def test_when_packet_does_not_contains_a_blacklisted_hotkey_should_allow_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
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
        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called()


class TestWrongSynapseRule(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_when_packet_contains_an_unknown_synapse_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
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
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Synapse name 'QnATask' not found, available ['Synapse', 'Score']",
        )

    @patch("builtins.open")
    @patch("time.time")
    def test_when_packet_contains_a_known_synapse_should_allow_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
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
            synapse="Synapse",
        )

        # Assert
        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called()


class TestVersionRule(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_when_packet_contains_outdated_version_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
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
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Neuron version 224 is outdated; version 225 is required.",
        )

    @patch("builtins.open")
    @patch("time.time")
    def test_when_packet_contains_required_version_should_allow_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
        }

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            specifications=specifications,
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
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
        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called()


class TestCustomRules(TestFirewall):
    @patch("builtins.open")
    @patch("time.time")
    def test_given_no_rules_when_hotkey_is_not_whitelisted_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
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
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )

    @patch("builtins.open")
    @patch("time.time")
    def test_given_no_rules_when_hotkey_is_whitelisted_should_accept_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=[])
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called()

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_custom_deny_rule_when_hotkey_is_not_whitelisted_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "ip": "192.168.0.1",
                "dport": 8091,
                "protocol": "tcp",
                "type": "deny",
            }
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

        # Assert
        assert 1 == len(firewall.ips_blocked)
        packet_mock.accept.assert_not_called()
        assert 2 == packet_mock.drop.call_count
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Deny ip",
        )

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_custom_deny_rule_when_hotkey_is_whitelisted_should_deny_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "ip": "192.168.0.1",
                "dport": 8091,
                "protocol": "tcp",
                "type": "deny",
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
        packet_mock.accept.assert_not_called()
        assert 2 == packet_mock.drop.call_count
        self.assert_blocked(
            firewall=firewall,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            type=RuleType.DENY,
            reason="Deny ip",
        )

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_custom_accept_rule_when_hotkey_is_not_whitelisted_should_accept_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "ip": "192.168.0.1",
                "dport": 8091,
                "protocol": "tcp",
                "type": "allow",
            }
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

        # Assert
        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called()

    @patch("builtins.open")
    @patch("time.time")
    def test_given_a_custom_accept_rule_when_hotkey_is_whitelisted_should_accept_the_request(
        self, mock_time, mock_open
    ):
        # Arrange
        observer = MagicMock()
        tool = MagicMock()
        packet_mock = MagicMock()

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        rules = [
            {
                "ip": "192.168.0.1",
                "dport": 8091,
                "protocol": "tcp",
                "type": "allow",
            }
        ]
        firewall = Firewall(observer=observer, tool=tool, interface="eth0", rules=rules)
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
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
        assert 0 == len(firewall.ips_blocked)
        assert 2 == packet_mock.accept.call_count
        packet_mock.drop.assert_not_called()
