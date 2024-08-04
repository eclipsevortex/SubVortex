# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import uuid
import time
import json
import datetime
from unittest.mock import patch, MagicMock

from subnet.firewall.firewall_model import RuleType
from subnet.miner.firewall import Firewall
from subnet.bittensor.synapse import Synapse
from subnet.protocol import Score

from tests.unit_tests.test_case import TestCase
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


class TestFirewall(TestCase):
    def setUp(self):
        self.counter = 0
        self.observer = MagicMock()
        self.tool = MagicMock()
        self.mock_packet = MagicMock()
        self.mock_time = patch("time.time").start()
        self.mock_json_file = patch("subnet.miner.firewall.load_njson_file").start()
        self.mock_json_file.return_value = {}
        self.mock_sse = patch("subnet.miner.firewall.SSEServer").start()
        self.mock_provider = patch("subnet.miner.firewall.FileLocalMonitor").start()
        self.mock_file_monitor = patch("subnet.miner.firewall.FirewallMonitor").start()
        self.mock_history_duration = patch(
            "subnet.miner.firewall.FIREWALL_REQUEST_HISTORY_DURATION", 120
        ).start()
        patcher = patch("uuid.uuid1", side_effect=self.generate_different_uuid)
        self.mock_uuid1 = patcher.start()
        self.patcher = patch("subnet.miner.firewall.Keypair")
        self.mock_keypair_class = self.patcher.start()
        self.mock_keypair = self.mock_keypair_class.return_value
        self.mock_keypair.verify.return_value = True
        self.mock_logging_success = patch(
            "subnet.miner.firewall.bt.logging.success"
        ).start()
        self.mock_logging_warning = patch(
            "subnet.miner.firewall.bt.logging.warning"
        ).start()

    def tearDown(self):
        patch.stopall()

    def assert_sources(self, firewall, count, queue_num = 1):
        source = firewall._sources[queue_num]
        assert count == len(source)

    def assert_requests(self, firewall, id, count, queue_num = 1):
        requests = firewall._sources[queue_num][id]
        assert count == len(requests)

    def assert_packet(
        self,
        firewall,
        packet_index,
        ip,
        port,
        protocol,
        type,
        flag,
        queue_num=1,
        reason=None,
        request_index=0,
    ):
        id = f"{ip}:{port}:{protocol}"
        requests = firewall._sources[queue_num].get(id)
        request = requests[request_index] if len(requests) > request_index else None
        packets = request._packets if request else None
        assert packets is not None
        packet = packets[packet_index] if len(packets) > packet_index else None
        assert packet is not None
        assert packet.flags == flag
        assert packet.type == type
        assert packet.reason == reason

    def assert_blocked(self, firewall, ip, port, protocol, type, reason):
        id = f"{ip}:{port}:{protocol}"
        packets = firewall._requests.get(id)
        if packets is None:
            return False

        packet = packets[-1] if len(packets) > 0 else None
        if packet is None:
            return False

        assert packet.type == type
        assert packet.reason == reason

    def create_firewall(self):
        return Firewall(
            observer=self.observer,
            tool=self.tool,
            sse=self.mock_sse,
            interface="eth0",
        )

    def generate_different_uuid(self):
        # Increment the counter to ensure unique UUIDs
        self.counter += 1

        # Generate a base time and convert to 100-nanosecond intervals
        base_time = datetime.datetime(2020, 1, 1) + datetime.timedelta(
            seconds=self.counter
        )
        timestamp = int(
            (base_time - datetime.datetime(1582, 10, 15)).total_seconds() * 1e7
        )

        # Create the UUID fields manually
        time_low = timestamp & 0xFFFFFFFF
        time_mid = (timestamp >> 32) & 0xFFFF
        time_hi_version = ((timestamp >> 48) & 0x0FFF) | (1 << 12)

        clock_seq = self.counter & 0x3FFF
        node = uuid.getnode()

        return uuid.UUID(
            fields=(
                time_low,
                time_mid,
                time_hi_version,
                clock_seq >> 8,
                clock_seq & 0xFF,
                node,
            )
        )

    def set_time(self, mock_time, second=0):
        mock_time.return_value = get_time(second)

    def set_rules(self, firewall, mock_open, rules=[]):
        data = json.dumps(rules)
        mock_open.return_value.__enter__.return_value.read.return_value = data

    def set_ip_blocked(self, ip_blocked=[]):
        self.mock_json_file.return_value = ip_blocked

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
        payload="",
        seconds=0,
    ):
        self.set_time(self.mock_time, seconds)
        packet = create_packet(
            src_ip,
            dst_ip,
            src_port,
            dst_port,
            seq,
            ack,
            flags,
            payload,
            self.mock_packet,
            self.mock_time,
        )
        firewall.packet_callback(packet)

    def send_request(
        self,
        src_ip,
        dst_ip,
        src_port,
        dst_port,
        firewall,
        seconds=[],
        seq=1000,
        synapse="Synapse",
        neuron_version=225,
        hotkey="5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja",
        initial_index=0,
    ):
        for index in range(0, len(seconds) // 2):
            # Step 1: SYN (Client to Server)
            self.send_packet(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                seq=seq + ((initial_index + index) * 2),
                ack=0,
                flags="S",
                firewall=firewall,
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
                seq=seq + ((initial_index + index) * 2) + 1,
                ack=1,
                flags="PA",
                payload=payload,
                firewall=firewall,
                seconds=seconds[index * 2 + 1],
            )


class TestPackets(TestFirewall):
    def test_given_no_rules_when_receiving_all_packets_for_tcp_requests_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
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
            seq=1001,
            ack=2001,
            flags="A",
            firewall=firewall,
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
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
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == self.mock_packet.accept.call_count
        assert 4 == self.mock_packet.drop.call_count

    def test_given_an_allow_rule_when_receiving_all_packets_for_tcp_requests_should_allow_all_of_them(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                }
            ],
        )
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
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
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
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.mock_packet.drop.assert_not_called()
        assert 6 == self.mock_packet.accept.call_count

    def test_given_a_deny_rule_when_receiving_all_packets_for_tcp_requests_should_deny_all_of_them(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "deny",
                }
            ],
        )
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
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
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
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DENY,
            reason="Deny ip",
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Deny ip",
        )
        assert 6 == self.mock_packet.drop.call_count
        self.mock_packet.accept.assert_not_called()

    def test_given_a_dos_rule_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                }
            ],
        )
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
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
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
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == self.mock_packet.accept.call_count
        assert 4 == self.mock_packet.drop.call_count

    def test_given_a_dos_rule_and_hotkey_whitelisted_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_of_them(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                }
            ],
        )
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
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
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
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.mock_packet.drop.assert_not_called()
        assert 6 == self.mock_packet.accept.call_count

    def test_given_a_dos_rule_when_receiving_all_packets_for_tcp_requests_triggering_an_alert_should_deny_all_of_them(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        self.mock_json_file.return_value = [
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430c8",
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.0.2",
                "dport": 8091,
                "flags": "S",
                "seq": client_seq - 2,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430c8",
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.0.2",
                "dport": 8091,
                "flags": "PA",
                "seq": client_seq - 1,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                }
            ],
        )
        firewall.run()

        seconds = 27

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
            seconds=seconds,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            seconds=seconds + 2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            seconds=seconds + 3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=seconds + 6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
            seconds=7,
        )

        # Step 9: ACK (Server to Client)

        # Step 10: FIN-ACK (Server to Client)
        server_seq += len(payload)

        # Step 11: ACK (Client to Server)
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_ack,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=seconds + 10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=2)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        assert 0 == self.mock_packet.accept.call_count
        assert 6 == self.mock_packet.drop.call_count

    def test_given_a_ddos_rule_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                }
            ],
        )
        firewall.run()

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            seconds=3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
            seconds=7,
        )

        # Step 9: ACK (Server to Client)

        # Step 10: FIN-ACK (Server to Client)
        server_seq += len(payload)

        # Step 11: ACK (Client to Server)
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_ack,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == self.mock_packet.accept.call_count
        assert 4 == self.mock_packet.drop.call_count

    def test_given_a_ddos_rule_and_hotkey_whitelisted_when_receiving_all_packets_for_tcp_requests_without_triggering_any_alert_should_allow_all_of_them(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                }
            ],
        )
        firewall.whitelist_hotkeys = [
            "5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"
        ]
        firewall.run()

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            seconds=3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
            seconds=7,
        )

        # Step 9: ACK (Server to Client)

        # Step 10: FIN-ACK (Server to Client)
        server_seq += len(payload)

        # Step 11: ACK (Client to Server)
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_ack,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.mock_packet.drop.assert_not_called()
        assert 6 == self.mock_packet.accept.call_count

    def test_given_a_ddos_rule_when_receiving_all_packets_for_tcp_requests_triggering_an_alert_should_deny_all_of_them(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        self.mock_json_file.return_value = [
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430c8",
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": client_seq,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430c8",
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": client_seq + 1,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430c9",
                "current_time": get_time(2),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": client_seq + 2,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430c9",
                "current_time": get_time(3),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": client_seq + 3,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430d1",
                "current_time": get_time(4),
                "sip": "192.168.0.2",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": client_seq + 4,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430d1",
                "current_time": get_time(5),
                "sip": "192.168.0.2",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": client_seq + 5,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430d2",
                "current_time": get_time(6),
                "sip": "192.168.0.3",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": client_seq + 6,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430d2",
                "current_time": get_time(7),
                "sip": "192.168.0.3",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": client_seq + 7,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430d3",
                "current_time": get_time(8),
                "sip": "192.168.0.4",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": client_seq + 8,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
            },
            {
                "request_id": "6fa459ea-ee8a-11d2-90d4-00c04fd430d3",
                "current_time": get_time(9),
                "sip": "192.168.0.4",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": client_seq + 9,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
        ]

        client_seq = client_seq + 10

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                }
            ],
        )
        firewall.run()

        seconds = 27

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
            seconds=seconds,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            seconds=seconds + 2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            seconds=seconds + 3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=seconds + 6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
            seconds=7,
        )

        # Step 9: ACK (Server to Client)

        # Step 10: FIN-ACK (Server to Client)
        server_seq += len(payload)

        # Step 11: ACK (Client to Server)
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_ack,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=seconds + 10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=4)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=3)
        self.assert_requests(firewall=firewall, id="192.168.0.2:8091:tcp", count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.3:8091:tcp", count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.4:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DDOS,
            reason="DDoS attack detected: 3 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DDOS,
            reason="DDoS attack detected: 3 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.3",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.3",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.4",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.4",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 0 == self.mock_packet.accept.call_count
        assert 6 == self.mock_packet.drop.call_count

    def test_given_a_whitelist_hotkey_when_receiving_all_packets_for_tcp_requests_should_allow_all_of_them(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        # Step 1: SYN (Client to Server)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="S",
            firewall=firewall,
        )

        # Step 2: SYN-ACK (Server to Client)

        # Step 3: ACK (Client to Server)
        client_seq += 1
        client_ack = server_seq + 1
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            firewall=firewall,
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="PA",
            payload=payload,
            firewall=firewall,
            seconds=3,
        )

        # Step 5: ACK (Server to Client)

        # Step 6: PSH-ACK (Server to Client - Response Data)
        payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nMock answer!"

        # Step 7: ACK (Client to Server)
        client_ack = server_seq + len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="A",
            payload=payload,
            firewall=firewall,
            seconds=6,
        )

        # Step 8: FIN-ACK (Client to Server)
        client_seq += len(payload)
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            seq=client_seq,
            ack=client_ack,
            flags="FA",
            payload=payload,
            firewall=firewall,
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
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.mock_packet.drop.assert_not_called()
        assert 6 == self.mock_packet.accept.call_count

    def test_given_a_blacklist_hotkey_when_receiving_all_packets_for_tcp_requests_should_allow_all_the_ones_for_connection_establishment_and_denied_all_the_rest(
        self,
    ):
        # Arrange
        client_seq = 1000
        server_seq = 2000
        client_ack = 0

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
        )
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
            seconds=2,
        )

        # Step 4: PSH-ACK (Client to Server - Request Data)
        payload = "b'POST /Synapse HTTP/1.1\r\nHost: 192.168.0.2:8091\r\nname: Synapse\r\ntimeout: 5.0\r\nbt_header_axon_ip: 192.168.2\r\nbt_header_axon_port: 8091\r\nbt_header_axon_hotkey: 5EUyagbvnJQwjEmTmdbiVtGqPzVNxZAreJBoFyTsYSpWX8x1\r\nbt_header_dendrite_ip: 192.168.0.1\r\nbt_header_dendrite_version: 7002000\r\nbt_header_dendrite_nonce: 1718696917604843780\r\nbt_header_dendrite_uuid: 085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a\r\nbt_header_dendrite_hotkey: 5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja\r\nbt_header_dendrite_signature: 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088\r\nbt_header_dendrite_neuron_version: 225\r\nheader_size: 640\r\ntotal_size: 3516\r\ncomputed_body_hash: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Python/3.10 aiohttp/3.9.5\r\nContent-Length: 797\r\nContent-Type: application/json\r\n\r\n'"
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
            seconds=10,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 2 == self.mock_packet.accept.call_count
        assert 4 == self.mock_packet.drop.call_count


class TestDoSRule(TestFirewall):
    def test_only_requests_within_time_window_are_kept(self):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 4,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[28, 29],
            initial_index=2,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=2)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[31, 32],
            initial_index=4,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=3)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )

    def test_given_a_dos_rule_when_a_dos_attack_is_detected_should_deny_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=2)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        assert 2 == self.mock_packet.accept.call_count  # Accept S/FA from first request
        assert 2 == self.mock_packet.drop.call_count  # Drop S/FA from second request

    def test_given_a_dos_rule_when_no_dos_attack_detected_should_allow_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1, 30, 31],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=2)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 4 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called

    def test_given_a_dos_rule_and_a_previous_request_denied_when_a_dos_attack_is_detected_should_deny_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=2)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        assert 2 == self.mock_packet.accept.call_count
        assert 2 == self.mock_packet.drop.call_count

        # Arrange
        self.mock_packet.reset_mock()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seq=2000,
            seconds=[56, 57],
        )

        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=3)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.mock_packet.accept.assert_not_called
        assert 2 == self.mock_packet.drop.call_count

    def test_given_a_dos_rule_and_a_previous_request_denied_when_not_dos_attack_is_detected_should_allow_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=2)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        assert 2 == self.mock_packet.accept.call_count
        assert 2 == self.mock_packet.drop.call_count

        # Arrange
        self.mock_packet.reset_mock()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seq=2000,
            seconds=[60, 61],
            initial_index=4,
        )

        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=3)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called


class TestDDoSRule(TestFirewall):
    def test_only_requests_within_time_window_are_kept(self):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 4,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )

        # Action
        self.send_request(
            src_ip="192.168.0.2",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[28, 29],
            initial_index=2,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=2)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.2:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )

        # Action
        self.send_request(
            src_ip="192.168.0.3",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[31, 32],
            initial_index=4,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=3)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.2:8091:tcp", count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.3:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.3",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.3",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )

    def test_given_a_ddos_rule_when_receive_less_requests_than_the_benchmark_within_the_time_window_should_allow_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 25,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        self.send_request(
            src_ip="192.168.0.2",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[25, 26],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=2)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.2:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 4 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called

    def test_given_a_ddos_rule_when_receive_more_requests_than_the_benchmark_within_the_time_window_but_does_not_trigger_ddos_attack_should_allow_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        self.send_request(
            src_ip="192.168.0.2",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[28, 29],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=2)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.2:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.2",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 4 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called

    def test_given_a_ddos_rule_when_receive_more_requests_than_the_benchmark_within_the_time_window_and_does_trigger_ddos_attack_should_deny_the_request(
        self,
    ):
        # Arrange
        events = []
        vps = [2, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        for j, (request_count) in enumerate(vps):
            ip = "192.168.0.{}".format(j + 1)
            for i in range(0, request_count):
                request_id = str(uuid.uuid1())
                events.append(
                    {
                        "request_id": request_id,
                        "id": f"{ip}:8091:tcp",
                        "current_time": get_time(j * 2 + i),
                        "sip": ip,
                        "sport": 7091,
                        "protocol": "tcp",
                        "dip": "192.168.1.1",
                        "dport": 8091,
                        "flags": "S",
                        "seq": 1000,
                        "ack": 0,
                        "max_time": 120,
                        "status": "allow",
                        "type": "ALLOW",
                    }
                )
                events.append(
                    {
                        "request_id": request_id,
                        "id": f"{ip}:8091:tcp",
                        "current_time": get_time(j * 2 + i + 1),
                        "sip": ip,
                        "sport": 7091,
                        "protocol": "tcp",
                        "dip": "192.168.1.1",
                        "dport": 8091,
                        "flags": "PA",
                        "seq": 1000,
                        "ack": 0,
                        "max_time": 120,
                        "status": "allow",
                        "type": "ALLOW",
                    }
                )

        self.mock_json_file.return_value = events

        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Action
        seconds = len(vps)
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
            initial_index=seconds * 2,
        )

        # Assert
        assert 1 == len(firewall._sources)
        assert 10 == len(firewall._sources[1])

        vps = [3, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        for j, (request_count) in enumerate(vps):
            ip = "192.168.0.{}".format(j + 1)
            assert vps[j] == len(firewall._sources[1][f"{ip}:8091:tcp"])

        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DDOS,
            reason="DDoS attack detected: 3 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DDOS,
            reason="DDoS attack detected: 3 requests in 30 seconds",
        )
        self.mock_packet.accept.assert_not_called
        assert 2 == self.mock_packet.drop.call_count

    def test_check_ddos_attacks(self):
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

        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 300,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )

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
                    firewall._sources.clear()

                    # Build the requests to load
                    events = []
                    for j, (request_count) in enumerate(vps):
                        ip = ip_template.format(j + 1)
                        for i in range(0, request_count):
                            if src_ip == ip and i == request_count - 1:
                                continue

                            request_id = str(uuid.uuid1())
                            events.append(
                                {
                                    "request_id": request_id,
                                    "id": f"{ip}:8091:tcp",
                                    "current_time": get_time(j * 2 + i),
                                    "sip": ip,
                                    "sport": 7091,
                                    "protocol": "tcp",
                                    "dip": "192.168.1.1",
                                    "dport": 8091,
                                    "flags": "S",
                                    "seq": 1000,
                                    "ack": 0,
                                    "max_time": 120,
                                    "status": "allow",
                                    "type": "ALLOW",
                                }
                            )
                            events.append(
                                {
                                    "request_id": request_id,
                                    "id": f"{ip}:8091:tcp",
                                    "current_time": get_time(j * 2 + i + 1),
                                    "sip": ip,
                                    "sport": 7091,
                                    "protocol": "tcp",
                                    "dip": "192.168.1.1",
                                    "dport": 8091,
                                    "flags": "PA",
                                    "seq": 1000,
                                    "ack": 0,
                                    "max_time": 120,
                                    "status": "allow",
                                    "type": "ALLOW",
                                }
                            )

                    self.mock_json_file.return_value = events

                    # Run the firewall
                    firewall.run()

                    # Action
                    seconds = len(vps)
                    self.send_request(
                        src_ip=src_ip,
                        dst_ip="192.168.1.1",
                        src_port=7091,
                        dst_port=8091,
                        firewall=firewall,
                        seconds=[0, 1],
                        initial_index=seconds * 2,
                    )

                    # Assert
                    for j, digit in enumerate(expect):
                        ip = ip_template.format(j + 1)
                        id = f"{ip}:8091:tcp"

                        requests = firewall._sources[1][id]
                        assert vps[j] == len(requests)

                        request = requests[-1]
                        assert (digit == "1") == request.is_denied()


class TestBlackListRule(TestFirewall):
    def test_when_packet_contains_a_blacklisted_hotkey_should_deny_the_request(self):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
            "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
        }

        firewall = self.create_firewall()
        firewall.update(specifications=specifications)
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 1 == self.mock_packet.accept.call_count
        assert 1 == self.mock_packet.drop.call_count

    def test_when_packet_does_not_contains_a_blacklisted_hotkey_should_allow_the_request(
        self,
    ):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
        }

        firewall = self.create_firewall()
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
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()


class TestWrongSynapseRule(TestFirewall):
    def test_when_packet_contains_an_unknown_synapse_should_deny_the_request(
        self,
    ):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
            "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
        }

        firewall = self.create_firewall()
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
            seconds=[0, 1],
            synapse="QnATask",
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Synapse name 'QnATask' not found, available ['Synapse', 'Score']",
        )
        assert 1 == self.mock_packet.accept.call_count
        assert 1 == self.mock_packet.drop.call_count

    def test_when_packet_contains_a_known_synapse_should_allow_the_request(self):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
            "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
        }

        firewall = self.create_firewall()
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
            seconds=[0, 1],
            synapse="Synapse",
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()


class TestSignatureRule(TestFirewall):
    def test_when_packet_contains_a_wrong_signature_should_deny_the_request(
        self,
    ):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
            "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
        }

        self.mock_keypair.verify.return_value = False

        firewall = self.create_firewall()
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
            seconds=[0, 1],
            synapse="Synapse",
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Signature mismatch with 1718696917604843780.5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja.0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045.085bdf0c-2d47-11ef-a8bd-07d2e5f8de9a.a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a and 0x7a57c4cdbcd604c667fa833afe795925e085642e272745d258d174c6f8268d1d30203c3a153ee952da83adefeb531a43fab69c46ddb6b9b6d17edeaf31380088",
        )
        assert 1 == self.mock_packet.accept.call_count
        assert 1 == self.mock_packet.drop.call_count

    def test_when_packet_contains_a_good_signature_should_allow_the_request(self):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
            "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
        }

        firewall = self.create_firewall()
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
            seconds=[0, 1],
            synapse="Synapse",
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()


class TestVersionRule(TestFirewall):
    def test_when_packet_contains_outdated_version_should_deny_the_request(self):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
            "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
        }

        firewall = self.create_firewall()
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
            seconds=[0, 1],
            neuron_version=224,
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Neuron version 224 is outdated; version 225 is required.",
        )
        assert 1 == self.mock_packet.accept.call_count
        assert 1 == self.mock_packet.drop.call_count

    def test_when_packet_contains_required_version_should_allow_the_request(self):
        # Arrange
        specifications = {
            "neuron_version": 225,
            "synapses": {"Synapse": Synapse, "Score": Score},
            "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
        }

        firewall = self.create_firewall()
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
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()


class TestAllowRule(TestFirewall):
    def test_given_an_accept_rule_when_hotkey_is_not_whitelisted_should_accept_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.update_config(
            [
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                }
            ],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        assert 1 == len(firewall._sources[1])
        assert 1 == len(firewall._sources[1]["192.168.0.1:8091:tcp"])
        assert 2 == len(firewall._sources[1]["192.168.0.1:8091:tcp"][0]._packets)
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()

    def test_given_an_accept_rule_when_hotkey_is_whitelisted_should_accept_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                }
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            },
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
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        assert 1 == len(firewall._sources[1])
        assert 1 == len(firewall._sources[1]["192.168.0.1:8091:tcp"])
        assert 2 == len(firewall._sources[1]["192.168.0.1:8091:tcp"][0]._packets)
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()

    def test_given_an_accept_rule_when_a_dos_attack_is_detected_should_accept_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            },
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
            seconds=[0, 1, 28, 29],
        )

        # Assert
        assert 1 == len(firewall._sources)
        assert 1 == len(firewall._sources[1])
        assert 2 == len(firewall._sources[1]["192.168.0.1:8091:tcp"])
        assert 2 == len(firewall._sources[1]["192.168.0.1:8091:tcp"][0]._packets)
        assert 2 == len(firewall._sources[1]["192.168.0.1:8091:tcp"][1]._packets)
        assert 4 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()

    def test_given_an_accept_rule_when_a_ddos_attack_is_detected_should_accept_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-ddos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # Arrange
        events = []
        vps = [2, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        for j, (request_count) in enumerate(vps):
            ip = "192.168.0.{}".format(j + 1)
            for i in range(0, request_count):
                request_id = str(uuid.uuid1())
                events.append(
                    {
                        "request_id": request_id,
                        "id": f"{ip}:8091:tcp",
                        "current_time": get_time(j * 2 + i),
                        "sip": ip,
                        "sport": 7091,
                        "protocol": "tcp",
                        "dip": "192.168.1.1",
                        "dport": 8091,
                        "flags": "S",
                        "seq": 1000,
                        "ack": 0,
                        "max_time": 120,
                        "status": "allow",
                        "type": "ALLOW",
                    }
                )
                events.append(
                    {
                        "request_id": request_id,
                        "id": f"{ip}:8091:tcp",
                        "current_time": get_time(j * 2 + i + 1),
                        "sip": ip,
                        "sport": 7091,
                        "protocol": "tcp",
                        "dip": "192.168.1.1",
                        "dport": 8091,
                        "flags": "PA",
                        "seq": 1000,
                        "ack": 0,
                        "max_time": 120,
                        "status": "allow",
                        "type": "ALLOW",
                    }
                )

        self.mock_json_file.return_value = events

        # Action
        seconds = len(vps)
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[seconds, seconds + 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        assert 1 == len(firewall._sources[1])
        assert 1 == len(firewall._sources[1]["192.168.0.1:8091:tcp"])
        assert 2 == len(firewall._sources[1]["192.168.0.1:8091:tcp"][0]._packets)
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()


class TestDenyRule(TestFirewall):
    def test_given_a_custom_deny_rule_when_hotkey_is_not_whitelisted_should_deny_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.update_config(
            [
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "deny",
                }
            ],
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        # Assert
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DENY,
            reason="Deny ip",
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Deny ip",
        )
        self.mock_packet.accept.assert_not_called()
        assert 2 == self.mock_packet.drop.call_count

    def test_given_a_custom_deny_rule_when_hotkey_is_whitelisted_should_deny_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.update_config(
            [
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "deny",
                }
            ]
        )
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
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DENY,
            reason="Deny ip",
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Deny ip",
        )
        self.mock_packet.accept.assert_not_called()
        assert 2 == self.mock_packet.drop.call_count


class TestNoRules(TestFirewall):
    def test_given_no_rules_when_hotkey_is_not_whitelisted_should_deny_the_request(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.run()

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DENY,
            reason="Hotkey '5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja' is blacklisted",
        )
        assert 1 == self.mock_packet.accept.call_count
        assert 1 == self.mock_packet.drop.call_count

    def test_given_no_rules_when_hotkey_is_whitelisted_should_accept_the_request(self):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
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
            seconds=[0, 1],
        )

        # Assert
        assert 1 == len(firewall._sources)
        self.assert_sources(firewall=firewall, count=1)
        self.assert_requests(firewall=firewall, id="192.168.0.1:8091:tcp", count=1)
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()


class TestIpBlockedFile(TestFirewall):
    def test_given_no_ips_blocked_when_starting_should_restore_nothing(self):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
        )

        # Action
        firewall.run()

        # Assert
        assert 0 == len(firewall._sources)

    def test_given_ips_blocked_saved_when_starting_should_restore_them(self):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": 1716894001.0,
                "sip": "65.109.75.3",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "queue_num": 1,
                "status": "deny",
                "type": "DENY",
                "reason": "Deny ip",
            },
            {
                "request_id": request_id,
                "current_time": 1716894002.0,
                "sip": "65.109.75.3",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "queue_num": 1,
                "status": "deny",
                "type": "DENY",
                "reason": "Synapse name 'QnATask' not found, available ['Synapse', 'Score']",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
        )

        # Action
        firewall.run()

        # Assert
        assert 1 == len(firewall._sources)  # one source
        source = firewall._sources[1]
        assert 1 == len(source["65.109.75.3:8091:tcp"])  # one request

        packets = source["65.109.75.3:8091:tcp"][0]._packets
        assert 2 == len(packets)  # 2 packets

        # SYNC Packet
        assert "65.109.75.3" == packets[0].sip
        assert 8091 == packets[0].dport
        assert "tcp" == packets[0].protocol
        assert RuleType.DENY == packets[0].type
        assert "deny" == packets[0].status
        assert "Deny ip" == packets[0].reason
        assert 1716894001.0 == packets[0].current_time

        # DATA Packet
        assert "65.109.75.3" == packets[1].sip
        assert 8091 == packets[1].dport
        assert "tcp" == packets[1].protocol
        assert RuleType.DENY == packets[1].type
        assert "deny" == packets[1].status
        assert (
            "Synapse name 'QnATask' not found, available ['Synapse', 'Score']"
            == packets[1].reason
        )
        assert 1716894002.0 == packets[1].current_time

    def test_given_ips_blocked_by_dos_saved_when_a_dos_attack_is_detected_should_keep_block_the_ips(
        self,
    ):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "queue_num": 1,
                "status": "deny",
                "type": "DETECT_DOS",
                "reason": "DoS attack detected: 2 requests in 30 seconds",
            },
            {
                "request_id": request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "queue_num": 1,
                "status": "deny",
                "type": "DETECT_DOS",
                "reason": "DoS attack detected: 2 requests in 30 seconds",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"]
        )
        firewall.run()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[4, 5],
            initial_index=4,
        )

        # Assert
        assert 1 == len(firewall._sources)
        source = firewall._sources[1]
        assert 2 == len(source["192.168.0.1:8091:tcp"])
        self.assert_packet(
            firewall=firewall,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )
        self.assert_packet(
            firewall=firewall,
            request_index=1,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.DETECT_DOS,
            reason="DoS attack detected: 2 requests in 30 seconds",
        )

        self.mock_packet.accept.assert_not_called
        assert 2 == self.mock_packet.drop.call_count

    def test_given_ips_blocked_by_dos_saved_when_an_allow_rule_is_applied_and_then_replaced_by_a_dos_rule_that_is_triggered_should_unblock_the_ips(
        self,
    ):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "queue_num": 1,
                "status": "deny",
                "type": "DENY",
                "reason": "Deny ip",
            },
            {
                "request_id": request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "queue_num": 1,
                "status": "deny",
                "type": "DENY",
                "reason": "Synapse name 'QnATask' not found, available ['Synapse', 'Score']",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
        ]

        firewall = self.create_firewall()
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045"
            },
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
        )
        firewall.run()

        # ALLOW rule replacing the DoS one
        firewall.update_config(
            [
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                }
            ]
        )

        # Senc request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[4, 5],
            initial_index=4,
        )

        # Assert
        assert 1 == len(firewall._sources)
        source = firewall._sources[1]
        assert 2 == len(source["192.168.0.1:8091:tcp"])
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()

        # Reset mock
        self.mock_packet.reset_mock()

        # DoS rule replacing the ALLOW one
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )

        # Action
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[34, 35],
            initial_index=7,
        )

        # Assert
        assert 1 == len(firewall._sources)
        assert 3 == len(source["192.168.0.1:8091:tcp"])
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=0,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="S",
            type=RuleType.ALLOW,
        )
        self.assert_packet(
            firewall=firewall,
            request_index=2,
            packet_index=1,
            ip="192.168.0.1",
            port=8091,
            protocol="tcp",
            flag="PA",
            type=RuleType.ALLOW,
        )
        assert 2 == self.mock_packet.accept.call_count
        self.mock_packet.drop.assert_not_called()


class TestRequest(TestFirewall):
    def test_given_a_request_when_receiving_another_request_before_cleaning_should_set_the_previous_id(
        self,
    ):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "queue_num": 1,
                "status": "allow",
                "type": "ALLOW",
            },
            {
                "request_id": request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "queue_num": 1,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.update_config(
            [
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                }
            ],
        )
        firewall.run()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
            initial_index=4,
        )

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 2 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert request_id == first_request.id
        assert None == first_request.previous_id

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id

    def test_given_a_request_when_receiving_another_request_after_cleaning_should_set_the_previous_id(
        self,
    ):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
                "queue_num": 1,
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.update_config(
            [
                {
                    "ip": "192.168.0.1",
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "allow",
                }
            ],
        )
        firewall.run()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[130, 131],
            initial_index=4,
        )

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 1 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id


class TestNotification(TestFirewall):
    def test_given_a_sync_allowed_when_a_new_request_denied_is_received_should_not_notify_ther_user(
        self,
    ):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
                "synapses": {"Synapse": Synapse, "Score": Score},
            },
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.run()

        first_request_id = firewall._sources[1]["192.168.0.1:8091:tcp"][0].id

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[2, 3],
            synapse="QnATask",
            initial_index=2,
        )

        self.mock_logging_warning.assert_called_once()
        self.mock_logging_success.assert_not_called()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 2 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id
        assert "allow" == first_request.status

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request_id == second_request.previous_id
        assert "deny" == second_request.status

    def test_given_a_sync_and_data_denied_then_a_sync_allowed_when_a_new_sync_denied_is_received_should_not_notify_ther_user(
        self,
    ):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "status": "deny",
                "type": "DETECT_DOS",
                "reason": "DoS attack detected: 5 requests in 300 seconds",
                "queue_num": 1,
            },
            {
                "request_id": request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "status": "deny",
                "type": "DETECT_DOS",
                "reason": "DoS attack detected: 5 requests in 300 seconds",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
                "queue_num": 1,
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 2,
                    },
                },
            ],
        )
        firewall.run()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync request
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1010,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=2,
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync request
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1030,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=3,
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 3 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id
        assert "deny" == first_request.status

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id
        assert "allow" == second_request.status

        third_request = source["192.168.0.1:8091:tcp"][2]
        assert second_request.id == third_request.previous_id
        assert "deny" == third_request.status

    def test_given_a_sync_and_data_denied_then_a_sync_allowed_when_a_new_sync_allowed_is_received_should_not_notify_ther_user(
        self,
    ):
        # Arrange
        request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "status": "deny",
                "type": "DETECT_DOS",
                "reason": "DoS attack detected: 5 requests in 300 seconds",
                "queue_num": 1,
            },
            {
                "request_id": request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "max_time": 120,
                "status": "deny",
                "type": "DETECT_DOS",
                "reason": "DoS attack detected: 5 requests in 300 seconds",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
                "queue_num": 1,
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            }
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 2,
                    },
                },
            ],
        )
        firewall.run()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync request
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1010,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=2,
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync request
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1030,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=32,
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 3 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id
        assert "deny" == first_request.status

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id
        assert "allow" == second_request.status

        third_request = source["192.168.0.1:8091:tcp"][2]
        assert second_request.id == third_request.previous_id
        assert "allow" == third_request.status

    def test_given_a_sync_and_data_allowed_then_a_sync_denied_when_a_new_sync_denied_is_received_should_notify_ther_user(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            },
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.run()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync packet
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1010,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=2,
        )

        self.mock_logging_warning.assert_called_once()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync packet
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1030,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=30,
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 3 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id
        assert "allow" == first_request.status

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id
        assert "deny" == second_request.status

        third_request = source["192.168.0.1:8091:tcp"][2]
        assert second_request.id == third_request.previous_id
        assert "deny" == third_request.status

    def test_given_a_sync_and_data_allowed_then_a_sync_denied_when_a_new_sync_allowed_is_received_should_notify_ther_user(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
            },
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.run()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync packet
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1010,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=2,
        )

        self.mock_logging_warning.assert_called_once()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync packet
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1030,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=32,
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 3 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id
        assert "allow" == first_request.status

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id
        assert "deny" == second_request.status

        third_request = source["192.168.0.1:8091:tcp"][2]
        assert second_request.id == third_request.previous_id
        assert "allow" == third_request.status

    def test_given_a_request_denied_when_a_new_request_denied_is_received_should_notify_ther_user(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
                "synapses": {"Synapse": Synapse, "Score": Score},
            },
        )
        firewall.run()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
            synapse="QnATask",
        )

        self.mock_logging_warning.assert_called_once()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[2, 3],
            synapse="QnATask",
            initial_index=2,
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 2 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id
        assert "deny" == first_request.status

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id
        assert "deny" == second_request.status

    def test_given_a_request_allowed_when_a_sync_packet_denied_is_received_should_notify_ther_user(
        self,
    ):
        # Arrange
        firewall = self.create_firewall()
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
                "synapses": {"Synapse": Synapse, "Score": Score},
            },
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 1,
                    },
                },
            ],
        )
        firewall.run()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send request
        self.send_request(
            src_ip="192.168.0.1",
            dst_ip="192.168.1.1",
            src_port=7091,
            dst_port=8091,
            firewall=firewall,
            seconds=[0, 1],
        )

        self.mock_logging_warning.assert_not_called()
        self.mock_logging_success.assert_not_called()

        self.mock_logging_warning.reset_mock()
        self.mock_logging_success.reset_mock()

        # Send Sync request
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1030,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=3,
        )

        self.mock_logging_warning.assert_called_once()
        self.mock_logging_success.assert_not_called()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 2 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id
        assert "allow" == first_request.status

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id
        assert "deny" == second_request.status


class TestPreviousRequest(TestFirewall):
    def test_give_previous_requests_when_a_new_sync_packet_is_allowed_should_assign_its_previous_request_id(
        self,
    ):
        # Arrange
        first_request_id = str(uuid.uuid1())
        second_request_id = str(uuid.uuid1())
        self.mock_json_file.return_value = [
            {
                "request_id": first_request_id,
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 790168449,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": first_request_id,
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 790168450,
                "ack": 2155942964,
                "max_time": 120,
                "status": "deny",
                "type": "DENY",
                "reason": "Synapse name 'QnATask' not found, available ['Synapse', 'Score']",
                "payload": "UE9TVCAvU3luYXBzZSBIVFRQLzEuMQ0KSG9zdDogMTkyLjE2OC4xLjE6ODA5MQ0KbmFtZTogU3luYXBzZQ0KdGltZW91dDogNS4wDQpidF9oZWFkZXJfYXhvbl9pcDogMTkyLjE2OC4xLjENCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUVVeWFnYnZuSlF3akVtVG1kYmlWdEdxUHpWTnhaQXJlSkJvRnlUc1lTcFdYOHgxDQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNjguMC4xDQpidF9oZWFkZXJfZGVuZHJpdGVfdmVyc2lvbjogNzAwMjAwMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNzE4Njk2OTE3NjA0ODQzNzgwDQpidF9oZWFkZXJfZGVuZHJpdGVfdXVpZDogMDg1YmRmMGMtMmQ0Ny0xMWVmLWE4YmQtMDdkMmU1ZjhkZTlhDQpidF9oZWFkZXJfZGVuZHJpdGVfaG90a2V5OiA1RG5nTlVwdjVrU3ZpMWdGNTdLWUNFTGV6UFZIU0N0ZFVqc2pnWXJYRWdkalU0SmENCmJ0X2hlYWRlcl9kZW5kcml0ZV9zaWduYXR1cmU6IDB4N2E1N2M0Y2RiY2Q2MDRjNjY3ZmE4MzNhZmU3OTU5MjVlMDg1NjQyZTI3Mjc0NWQyNThkMTc0YzZmODI2OGQxZDMwMjAzYzNhMTUzZWU5NTJkYTgzYWRlZmViNTMxYTQzZmFiNjljNDZkZGI2YjliNmQxN2VkZWFmMzEzODAwODgNCmJ0X2hlYWRlcl9kZW5kcml0ZV9uZXVyb25fdmVyc2lvbjogMjI1DQpoZWFkZXJfc2l6ZTogNjQwDQp0b3RhbF9zaXplOiAzNTE2DQpjb21wdXRlZF9ib2R5X2hhc2g6IGE3ZmZjNmY4YmYxZWQ3NjY1MWMxNDc1NmEwNjFkNjYyZjU4MGZmNGRlNDNiNDlmYTgyZDgwYTRiODBmODQzNGENCkFjY2VwdDogKi8qDQpBY2NlcHQtRW5jb2Rpbmc6IGd6aXAsIGRlZmxhdGUNClVzZXItQWdlbnQ6IFB5dGhvbi8zLjEwIGFpb2h0dHAvMy45LjUNCkNvbnRlbnQtTGVuZ3RoOiA3OTcNCkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbg0KDQo=",
                "queue_num": 1,
            },
            {
                "request_id": second_request_id,
                "previous_id": first_request_id,
                "current_time": get_time(2),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 3748722150,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
        ]

        firewall = self.create_firewall()
        firewall.update(
            whitelist_hotkeys=["5DngNUpv5kSvi1gF57KYCELezPVHSCtdUjsjgYrXEgdjU4Ja"],
            specifications={
                "hotkey": "0x4c3f89c1317781d73914bd4e3b11ef3ebcff86def08033def85db3d004899045",
                "synapses": {"Synapse": Synapse, "Score": Score},
            },
        )
        firewall.update_config(
            [
                {
                    "dport": 8091,
                    "protocol": "tcp",
                    "type": "detect-dos",
                    "configuration": {
                        "time_window": 30,
                        "packet_threshold": 2,
                    },
                },
            ],
        )
        firewall.run()

        # Action
        self.send_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=2864050829,
            ack=0,
            flags="S",
            firewall=firewall,
            seconds=4,
        )

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]
        assert 3 == len(source["192.168.0.1:8091:tcp"])

        first_request = source["192.168.0.1:8091:tcp"][0]
        assert None == first_request.previous_id

        second_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == second_request.previous_id

        # Previous of the 3rd request as to be the first previous request with
        # SYNC packet if denided
        # DATA packet otherwise
        third_request = source["192.168.0.1:8091:tcp"][1]
        assert first_request.id == third_request.previous_id


class TestReloadSource(TestFirewall):
    def test_reload_sources_correctly(self):
        # Arrange
        self.mock_json_file.return_value = [
            {
                "request_id": "3c600194-4362-11ef-b64f-9dc9db5f9ad8",
                "current_time": get_time(0),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1000,
                "ack": 0,
                "max_time": 120,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": "3c600194-4362-11ef-b64f-9dc9db5f9ad8",
                "current_time": get_time(1),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1001,
                "ack": 1,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": "40edacde-4362-11ef-b64f-9dc9db5f9ad8",
                "previous_id": "3c600194-4362-11ef-b64f-9dc9db5f9ad8",
                "current_time": get_time(2),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1010,
                "ack": 0,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": "40edacde-4362-11ef-b64f-9dc9db5f9ad8",
                "previous_id": "3c600194-4362-11ef-b64f-9dc9db5f9ad8",
                "current_time": get_time(3),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1011,
                "ack": 1,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": "45df6cdc-4362-11ef-b64f-9dc9db5f9ad8",
                "previous_id": "40edacde-4362-11ef-b64f-9dc9db5f9ad8",
                "current_time": get_time(4),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "S",
                "seq": 1020,
                "ack": 0,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
            {
                "request_id": "45df6cdc-4362-11ef-b64f-9dc9db5f9ad8",
                "previous_id": "40edacde-4362-11ef-b64f-9dc9db5f9ad8",
                "current_time": get_time(5),
                "sip": "192.168.0.1",
                "sport": 7091,
                "protocol": "tcp",
                "dip": "192.168.1.1",
                "dport": 8091,
                "flags": "PA",
                "seq": 1021,
                "ack": 1,
                "status": "allow",
                "type": "ALLOW",
                "queue_num": 1,
            },
        ]

        firewall = self.create_firewall()
        firewall.run()

        # Assert
        assert 1 == len(firewall._sources)

        source = firewall._sources[1]

        requests = source["192.168.0.1:8091:tcp"]
        assert 3 == len(requests)

        assert "3c600194-4362-11ef-b64f-9dc9db5f9ad8" == requests[0].id
        assert None == requests[0].previous_id
        assert "192.168.0.1:8091:1000:0:S" == requests[0]._packets[0].internal_id
        assert "192.168.0.1:8091:1001:1:PA" == requests[0]._packets[1].internal_id

        assert "40edacde-4362-11ef-b64f-9dc9db5f9ad8" == requests[1].id
        assert "3c600194-4362-11ef-b64f-9dc9db5f9ad8" == requests[1].previous_id
        assert "192.168.0.1:8091:1010:0:S" == requests[1]._packets[0].internal_id
        assert "192.168.0.1:8091:1011:1:PA" == requests[1]._packets[1].internal_id

        assert "45df6cdc-4362-11ef-b64f-9dc9db5f9ad8" == requests[2].id
        assert "40edacde-4362-11ef-b64f-9dc9db5f9ad8" == requests[2].previous_id
        assert "192.168.0.1:8091:1020:0:S" == requests[2]._packets[0].internal_id
        assert "192.168.0.1:8091:1021:1:PA" == requests[2]._packets[1].internal_id
