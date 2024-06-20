from subnet.shared.platform import is_linux_platform
from subnet.firewall.firewall_observer import FirewallObserver
from subnet.firewall.firewall_packet import FirewallPacket

if is_linux_platform():
    from netfilterqueue import NetfilterQueue  # type: ignore


class FirewallLinuxObserver(FirewallObserver):
    def __init__(self) -> None:
        self._nfqueue = NetfilterQueue()

    def subscribe(self, *args, **kwargs):
        queue_num = kwargs.get("queue_num", None)
        if not queue_num:
            raise ValueError("Provide queue_num")

        callback = kwargs.get("callback", None)
        if not queue_num:
            raise ValueError("Provide callback")

        self._callback = callback
        self._nfqueue.bind(queue_num, self._packet_callback)

    def start(self):
        self._nfqueue.run()

    def stop(self):
        self._nfqueue.unbind()

    def _packet_callback(self, packet):
        try:
            instance = FirewallPacket(packet)
            if not self._callback:
                return

            self._callback(instance)
        except Exception:
            pass
