from abc import ABC, abstractmethod


class FirewallObserver(ABC):
    @abstractmethod
    def subscribe(self, *args, **kwargs):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def _packet_callback(self, packet):
        pass
