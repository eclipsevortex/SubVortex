import re
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


class FirewallTool(ABC):
    @abstractmethod
    def rule_exists(self, ip=None, sport=None, dport=None, protocol="tcp", allow=True):
        pass

    @abstractmethod
    def create_allow_loopback_rule(self):
        pass

    @abstractmethod
    def create_deny_policy(self):
        pass

    @abstractmethod
    def create_allow_rule(self, ip=None, sport=None, dport=None, protocol="tcp"):
        pass

    @abstractmethod
    def create_deny_rule(self, ip=None, sport=None, dport=None, protocol="tcp"):
        pass

    @abstractmethod
    def remove_rule(self, ip=None, sport=None, dport=None, protocol="tcp", allow=True):
        pass


def is_valid_number(value):
    """
    True if the value is a valid number, false otherwise
    """
    data = str(value) if value else ""
    return bool(re.match(r"^[1-9]\d*$", data))


# We authorise only TCP as it is the only protocol used in the bittensor world
def is_valid_protocol(protocol):
    """
    True if the protocol is valid, false otherwise
    Match tcp
    """
    return protocol.lower() in ["tcp"]


def is_valid_port(port):
    """
    True if the port is valid, false otherwise
    Match 1 to 5 digits
    """
    port_pattern = re.compile(r"^\d{1,5}$")
    return bool(port_pattern.match(str(port))) and 1 <= int(port) <= 65535


def is_valid_ip(ip):
    """
    True if the ip is valid, false otherwise
    Match xxx.xxx.xxx.xxx format
    """
    ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
    if ip_pattern.match(ip):
        parts = ip.split(".")
        if all(0 <= int(part) <= 255 for part in parts):
            return True
    return False


class RuleType(Enum):
    ALLOW = "allow"
    DENY = "deny"
    DETECT_DOS = "detect-dos"
    DETECT_DDOS = "detect-ddos"


@dataclass
class Rule(ABC):
    def __init__(self, ip=None, sport=None, dport=None, protocol=None):
        self.ip = ip
        self.sport = sport
        self.dport = dport
        self.protocol = protocol

    @staticmethod
    @abstractmethod
    def create(config={}):
        pass

    @property
    @abstractmethod
    def rule_type(self):
        pass


@dataclass
class AllowRule(Rule):
    """
    Define the rule to allow access
    """

    def __init__(self, ip=None, sport=None, dport=None, protocol=None):
        super().__init__(ip=ip, sport=sport, dport=dport, protocol=protocol)

    @staticmethod
    def create(config={}):
        ip = config.get("ip")
        sport = config.get("sport")
        dport = config.get("dport")
        protocol = config.get("protocol")

        if ip is not None and not is_valid_ip(ip):
            raise ValueError(f"Invalid IP address: {ip}")

        if sport is not None and not is_valid_port(sport):
            raise ValueError(f"Invalid Port: {sport}")

        if dport is not None and not is_valid_port(dport):
            raise ValueError(f"Invalid Port: {dport}")

        port = sport or dport
        if ip is None and port is None:
            raise ValueError("Ip and or Port have to be provided")

        if protocol and not is_valid_protocol(protocol):
            raise ValueError(f"Invalid Protocol: {protocol}")

        return AllowRule(
            ip=ip,
            sport=sport,
            dport=dport,
            protocol=protocol,
        )

    @property
    def rule_type(self):
        return RuleType.ALLOW


@dataclass
class DenyRule(Rule):
    """
    Define the rule to deny access
    """

    def __init__(self, ip=None, sport=None, dport=None, protocol=None):
        super().__init__(ip=ip, sport=sport, dport=dport, protocol=protocol)

    @staticmethod
    def create(config={}):
        ip = config.get("ip")
        sport = config.get("sport")
        dport = config.get("dport")
        protocol = config.get("protocol")

        if ip is not None and not is_valid_ip(ip):
            raise ValueError(f"Invalid IP address: {ip}")

        if sport is not None and not is_valid_port(sport):
            raise ValueError(f"Invalid Port: {sport}")

        if dport is not None and not is_valid_port(dport):
            raise ValueError(f"Invalid Port: {dport}")

        port = sport or dport
        if ip is None and port is None:
            raise ValueError("Ip and or Port have to be provided")

        if protocol and not is_valid_protocol(protocol):
            raise ValueError(f"Invalid Protocol: {protocol}")

        return DenyRule(
            ip=ip,
            sport=sport,
            dport=dport,
            protocol=protocol,
        )

    @property
    def rule_type(self):
        return RuleType.DENY


@dataclass
class DetectDoSRule(Rule):
    """
    Define the rule to detect a DoS attack
    """

    def __init__(self, dport, protocol, time_window, packet_threshold):
        super().__init__(dport=dport, protocol=protocol)

        self.time_window = time_window
        self.packet_threshold = packet_threshold

    @staticmethod
    def create(config={}):
        dport = config.get("dport")
        protocol = config.get("protocol")
        configuration = config.get("configuration") or {}
        time_window = configuration.get("time_window")
        packet_threshold = configuration.get("packet_threshold")

        if dport is None:
            raise ValueError("Port have to be provided")

        if not is_valid_port(dport):
            raise ValueError(f"Invalid Port: {dport}")

        if protocol is not None and not is_valid_protocol(protocol):
            raise ValueError(f"Invalid Protocol: {protocol}")

        if not is_valid_number(time_window):
            raise ValueError(f"Invalid Time Window: {time_window}")

        if not is_valid_number(packet_threshold):
            raise ValueError(f"Invalid Packet Threashold: {packet_threshold}")

        return DetectDoSRule(
            dport=dport,
            protocol=protocol,
            time_window=time_window,
            packet_threshold=packet_threshold,
        )

    @property
    def rule_type(self):
        return RuleType.DETECT_DOS


@dataclass
class DetectDDoSRule(Rule):
    """
    Define the rule to detect a DDoS attack
    """

    def __init__(self, dport, protocol, time_window, packet_threshold):
        super().__init__(dport=dport, protocol=protocol)

        self.time_window = time_window
        self.packet_threshold = packet_threshold

    @staticmethod
    def create(config={}):
        dport = config.get("dport")
        protocol = config.get("protocol")
        configuration = config.get("configuration") or {}
        time_window = configuration.get("time_window")
        packet_threshold = configuration.get("packet_threshold")

        if dport is None:
            raise ValueError("Port have to be provided")

        if not is_valid_port(dport):
            raise ValueError(f"Invalid Port: {dport}")

        if protocol is not None and not is_valid_protocol(protocol):
            raise ValueError(f"Invalid Protocol: {protocol}")

        if not is_valid_number(time_window):
            raise ValueError(f"Invalid Time Window: {time_window}")

        if not is_valid_number(packet_threshold):
            raise ValueError(f"Invalid Packet Threashold: {packet_threshold}")

        return DetectDDoSRule(
            dport=dport,
            protocol=protocol,
            time_window=time_window,
            packet_threshold=packet_threshold,
        )

    @property
    def rule_type(self):
        return RuleType.DETECT_DDOS


def create_rule(config={}) -> Rule:
    if config.get("type") == "allow":
        return AllowRule.create(config)

    if config.get("type") == "deny":
        return DenyRule.create(config)

    if config.get("type") == "detect-dos":
        return DetectDoSRule.create(config)

    if config.get("type") == "detect-ddos":
        return DetectDDoSRule.create(config)
