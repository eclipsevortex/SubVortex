from abc import ABC, abstractmethod


class FirewallTool(ABC):
    @abstractmethod
    def rule_exists(
        self, ip=None, sport=None, dport=None, protocol="tcp", allow=True, queue=None
    ):
        pass

    @abstractmethod
    def create_allow_loopback_rule(self):
        pass

    @abstractmethod
    def create_deny_policy(self):
        pass

    @abstractmethod
    def create_allow_rule(
        self, ip=None, sport=None, dport=None, protocol="tcp", queue=None
    ):
        pass

    @abstractmethod
    def create_deny_rule(self, ip=None, sport=None, dport=None, protocol="tcp"):
        pass

    @abstractmethod
    def remove_rule(
        self, ip=None, sport=None, dport=None, protocol="tcp", allow=True, queue=None
    ):
        pass
