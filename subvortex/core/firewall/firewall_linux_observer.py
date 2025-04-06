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
import time
import threading

from subvortex.core.shared.platform import is_linux_platform
from subvortex.core.firewall.firewall_observer import FirewallObserver
from subvortex.core.firewall.firewall_packet import FirewallPacket

if is_linux_platform():
    from netfilterqueue import NetfilterQueue  # type: ignore


class FirewallLinuxObserver(FirewallObserver):
    def __init__(self) -> None:
        self._threads = []
        self._queues = []
        self._callbacks = {}

    def subscribe(self, *args, **kwargs):
        name = kwargs.get("name", None)

        queue_num = kwargs.get("queue_num", None)
        if not queue_num:
            raise ValueError("Provide queue_num")

        callback = kwargs.get("callback", None)
        if not queue_num:
            raise ValueError("Provide callback")

        queue = NetfilterQueue()
        queue.bind(queue_num, self._create_callback(queue_num))

        self._queues.append((name, queue))
        self._callbacks[queue_num] = callback

    def start(self):
        """
        Start all queue in a thread
        """
        for name, queue in self._queues:
            thread = threading.Thread(target=queue.run, name=name)
            thread.start()

            # Save the new thread to be able to stop it
            self._threads.append(thread)

    def stop(self):
        """
        Stop all the threads and unbind all the queue
        """
        # Unbind all queues
        for _, queue in self._queues:
            queue.unbind()

        # Stop all thread
        for thread in self._threads:
            if thread.is_alive():
                thread.join()

    def _create_callback(self, queue_num):
        def _packet_callback(packet):
            try:
                # Set the time of reception
                current_time = time.time()

                # Create a packet instance
                instance = FirewallPacket.from_packet(
                    packet=packet, current_time=current_time, queue_num=queue_num
                )

                callback = self._callbacks.get(queue_num)
                if not callback:
                    return

                callback(instance)
            except Exception:
                pass

        return _packet_callback
