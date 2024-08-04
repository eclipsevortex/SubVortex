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
import unittest
from unittest.mock import patch, MagicMock

from subnet.firewall.firewall_request import FirewallRequest

from tests.unit_tests.mocks.mock_packet import create_packet


class TestFirewallRequest(unittest.TestCase):
    def setUp(self):
        self.mock_packet = MagicMock()
        self.mock_time = patch("time.time").start()

    def tearDown(self):
        patch.stopall()

    def test_given_a_request_with_an_allowed_sync_packet_when_check_if_the_request_is_allowed_should_return_false(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allow"
        request.add_packet(packet)

        # Action
        result = request.is_allowed()

        # Assert
        assert False == result

    def test_given_a_request_with_a_denied_sync_packet_when_check_if_the_request_is_allowed_should_return_false(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "deny"
        request.add_packet(packet)

        # Action
        result = request.is_allowed()

        # Assert
        assert False == result

    def test_given_a_request_with_an_allowed_sync_and_data_packets_when_check_if_the_request_is_allowed_should_return_true(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allow"
        request.add_packet(packet)

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1002,
            ack=2002,
            flags="PA",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allow"
        request.add_packet(packet)

        # Action
        result = request.is_allowed()

        # Assert
        assert True == result

    def test_given_a_request_with_an_allowed_sync_packet_when_check_if_the_request_is_denied_should_return_false(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allow"
        request.add_packet(packet)

        # Action
        result = request.is_denied()

        # Assert
        assert False == result

    def test_given_a_request_with_a_denied_sync_packet_when_check_if_the_request_is_denied_should_return_true(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "deny"
        request.add_packet(packet)

        # Action
        result = request.is_denied()

        # Assert
        assert True == result

    def test_given_a_request_with_an_allowed_sync_and_data_packets_when_check_if_the_request_is_denied_should_return_false(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allowed"
        request.add_packet(packet)

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1002,
            ack=2002,
            flags="PA",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allow"
        request.add_packet(packet)

        # Action
        result = request.is_denied()

        # Assert
        assert False == result

    def test_given_a_request_with_an_allowed_sync_packet_and_a_denied_data_packet_when_check_if_the_request_is_denied_should_return_true(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allowed"
        request.add_packet(packet)

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1002,
            ack=2002,
            flags="PA",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "deny"
        request.add_packet(packet)

        # Action
        result = request.is_denied()

        # Assert
        assert True == result

    def test_given_a_request_when_all_the_packets_have_the_same_max_time_should_return_the_unique_max_time(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allowed"
        packet.max_time = 60
        request.add_packet(packet)

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1002,
            ack=2002,
            flags="PA",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allowed"
        packet.max_time = 60
        request.add_packet(packet)

        # Assert
        assert 60 == request.max_time

    def test_given_a_request_when_all_the_packets_have_different_max_time_should_return_the_max_time(
        self,
    ):
        # Arrange
        request = FirewallRequest()

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1001,
            ack=2001,
            flags="S",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allowed"
        packet.max_time = 60
        request.add_packet(packet)

        packet = create_packet(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.2",
            src_port=7091,
            dst_port=8091,
            seq=1002,
            ack=2002,
            flags="PA",
            payload="",
            mock_time=self.mock_time,
            packet_mock=self.mock_packet,
        )
        packet.status = "allowed"
        packet.max_time = 120
        request.add_packet(packet)

        # Assert
        assert 120 == request.max_time
