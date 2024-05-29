import unittest
from subnet.miner.firewall_models import AllowRule, DenyRule, DetectDoSRule, DetectDDoSRule


class TestAllowRule(unittest.TestCase):
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
        config = {"port": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
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
        assert None == rule.port
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "protocol": "tcp", "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert None == rule.port
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"port": 0, "protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            AllowRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Port: 0")

    def test_given_a_config_when_port_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {"port": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "port": 8091, "type": "allow"}

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.port
        assert None == rule.protocol

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "port": 8091,
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
            "port": 8091,
            "protocol": "tcp",
            "type": "allow",
        }

        # Action
        rule = AllowRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol


class TestDenyRule(unittest.TestCase):
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
        config = {"port": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
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
        assert None == rule.port
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "protocol": "tcp", "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert None == rule.port
        assert "tcp" == rule.protocol

    def test_given_a_config_when_port_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {"port": 0, "protocol": "tcp", "type": "allow"}

        # Action
        with self.assertRaises(ValueError) as cm:
            DenyRule.create(config)

        # Action / Assert
        self.assertEqual(str(cm.exception), "Invalid Port: 0")

    def test_given_a_config_when_port_is_formatted_correctly_should_create_the_rule(
        self,
    ):
        # Arrange
        config = {"port": 8091, "protocol": "tcp", "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {"ip": "192.168.10.1", "port": 8091, "type": "allow"}

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.port
        assert None == rule.protocol

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "port": 8091,
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
            "port": 8091,
            "protocol": "tcp",
            "type": "allow",
        }

        # Action
        rule = DenyRule.create(config)

        # Action / Assert
        assert "192.168.10.1" == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol


class TestDetectDoSRule(unittest.TestCase):
    def test_given_a_config_when_port_is_not_provided_should_raise_an_exception(self):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
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
            "port": 0,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {
            "port": 8091,
            "type": "detect-dos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert None == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "port": 8091,
            "protocol": "udp",
            "type": "detect-dos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_time_window_is_not_provided_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {
                "time_window": 0,
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-dos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold


class TestDetectDDoSRule(unittest.TestCase):
    def test_given_a_config_when_port_is_not_provided_should_raise_an_exception(self):
        # Arrange
        config = {
            "ip": "192.168.10.1",
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
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
            "port": 0,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_provided_should_create_the_rule(self):
        # Arrange
        config = {
            "port": 8091,
            "type": "detect-ddos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert None == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_protocol_is_not_formatted_correctly_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "port": 8091,
            "protocol": "udp",
            "type": "detect-ddos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

    def test_given_a_config_when_time_window_is_not_provided_should_raise_an_exception(
        self,
    ):
        # Arrange
        config = {
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {
                "time_window": 0,
                "packet_threshold": 1
            }
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
            "port": 8091,
            "protocol": "tcp",
            "type": "detect-ddos",
            "configuration": {
                "time_window": 30,
                "packet_threshold": 1
            }
        }

        # Action
        rule = DetectDDoSRule.create(config)

        # Action / Assert
        assert None == rule.ip
        assert 8091 == rule.port
        assert "tcp" == rule.protocol
        assert 30 == rule.time_window
        assert 1 == rule.packet_threshold

