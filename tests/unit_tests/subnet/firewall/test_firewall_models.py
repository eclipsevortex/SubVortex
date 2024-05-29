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
from subnet.firewall.firewall_model import (
    AllowRule,
    DenyRule,
    DetectDoSRule,
    DetectDDoSRule,
)

from tests.unit_tests.test_case import TestCase


class TestAllowRule(TestCase):
    def test_given_a_config_when_ip_and_port_are_not_provided_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            AllowRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Ip and or Port have to be provided")

    def test_given_a_config_when_ip_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"dport": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_ip_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"ip": "192.168", "protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            AllowRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid IP address: 192.168")

    def test_given_a_config_when_ip_is_formatted_correctly_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "protocol": "tcp", "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert None == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "protocol": "tcp", "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert None == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"dport": 0, "protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            AllowRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Port: 0")

    def test_given_a_config_when_port_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {"dport": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "dport": 8091, "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.dport
        assert None == rule.protocol

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "dport": 8091,
            "protocol": "udp",
            "type": "allow",
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            AllowRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Protocol: udp")

    def test_given_a_config_when_protocol_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "dport": 8091,
            "protocol": "tcp",
            "type": "allow",
        }

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol


class TestDenyRule(TestCase):
    def test_given_a_config_when_ip_and_port_are_not_provided_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            DenyRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Ip and or Port have to be provided")

    def test_given_a_config_when_ip_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"dport": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_ip_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"ip": "192.168", "protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            DenyRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid IP address: 192.168")

    def test_given_a_config_when_ip_is_formatted_correctly_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "protocol": "tcp", "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert None == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "protocol": "tcp", "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert None == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"dport": 0, "protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            DenyRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Port: 0")

    def test_given_a_config_when_port_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {"dport": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "dport": 8091, "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.dport
        assert None == rule.protocol

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "dport": 8091,
            "protocol": "udp",
            "type": "allow",
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DenyRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Protocol: udp")

    def test_given_a_config_when_protocol_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "dport": 8091,
            "protocol": "tcp",
            "type": "allow",
        }

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol


class TestDetectDoSRule(TestCase):
    def test_given_a_config_when_port_is_not_provided_should_raise_an_exception(self):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Port have to be provided")

    def test_given_a_config_when_port_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 0,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Port: 0")

    def test_given_a_config_when_port_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {
            "dport": 8091,
            "type": "detect-dos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert None == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "udp",
            "type": "detect-dos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Protocol: udp")

    def test_given_a_config_when_protocol_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_time_window_is_not_provided_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {"packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Time Window: None")

    def test_given_a_config_when_time_window_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {"time_window": 0, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Time Window: 0")

    def test_given_a_config_when_time_window_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold


class TestDetectDDoSRule(TestCase):
    def test_given_a_config_when_port_is_not_provided_should_raise_an_exception(self):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Port have to be provided")

    def test_given_a_config_when_port_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 0,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Port: 0")

    def test_given_a_config_when_port_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {
            "dport": 8091,
            "type": "detect-ddos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert None == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "udp",
            "type": "detect-ddos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Protocol: udp")

    def test_given_a_config_when_protocol_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_time_window_is_not_provided_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {"packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Time Window: None")

    def test_given_a_config_when_time_window_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {"time_window": 0, "packet_threshold": 1},
        }

        # Action
        with self.assertRaises(ValueError) as cm:
            DetectDDoSRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Time Window: 0")

    def test_given_a_config_when_time_window_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {
            "dport": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {"time_window": 30, "packet_threshold": 1},
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.dport
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold
