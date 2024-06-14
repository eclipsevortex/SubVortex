from abc import ABC, abstractmethod

class FirewallTool(ABC):
    @abstractmethod
    def rule_exists(self, ip=None, port=None, protocol="tcp", allow=True):
        pass

    @abstractmethod
    def allow_traffic_from_ip(self, ip):
        pass

    @abstractmethod
    def allow_traffic_on_port(self, port, protocol="tcp"):
        pass

    @abstractmethod
    def allow_traffic_from_ip_and_port(self, ip, port, protocol="tcp"):
        pass

    @abstractmethod
    def deny_traffic_from_ip(self, ip):
        pass

    @abstractmethod
    def deny_traffic_on_port(self, port, protocol):
        pass

    @abstractmethod
    def deny_traffic_from_ip_and_port(self, ip, port, protocol="tcp"):
        pass

    @abstractmethod
    def remove_deny_traffic_from_ip_and_port(self, ip, port, protocol="tcp"):
        pass