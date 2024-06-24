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
