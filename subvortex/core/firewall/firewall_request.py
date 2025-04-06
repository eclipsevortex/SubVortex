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
import uuid
from subvortex.core.firewall.firewall_packet import FirewallPacket

seq_space = 2**32  # 32-bit sequence space

# Assume typical packets are 1500 bytes (standard Ethernet MTU).
transaction_packet_size = 1500

# Estimate an average request/response size. For this example, assume 10 packets per transaction.
transaction_length = 10

window_size = transaction_packet_size * transaction_length


class FirewallRequest:
    def __init__(self, previous_id=None):
        self.id = str(uuid.uuid1())
        self.previous_id = previous_id
        self.notified = False
        self._packets: list[FirewallPacket] = []

    @property
    def group_id(self):
        return self._packets[0].id if len(self._packets) > 0 else None

    @property
    def queue_num(self):
        return self._packets[0].queue_num if len(self._packets) > 0 else None

    @property
    def current_time(self):
        packet = next((x for x in self._packets if x.flags == "S"), None)
        return packet.current_time if packet else 0

    @property
    def status(self):
        return "deny" if self.is_denied() else "allow"

    @property
    def max_time(self):
        return max([x.max_time for x in self._packets])

    def get_sync_packet(self):
        packet = self._packets[0] if len(self._packets) > 0 else None
        return packet if packet is not None and packet.flags == "S" else None

    def get_packet_by_internal_id(self, internal_id: str):
        return next((x for x in self._packets if x.internal_id == internal_id), None)

    def is_part_of(self, seq):
        """
        True if the packet is part of the request, false otherwise
        Check if a packet's sequence number falls within the valid range of a TCP connection by comparing
        it to the initial sequence number and the upper limit, handling the wrap-around of the 32-bit sequence number space.
        """
        sync_packet = self.get_sync_packet()
        if sync_packet is None:
            return False

        upper_limit = (sync_packet.seq + window_size) % seq_space

        if sync_packet.seq <= upper_limit:
            return sync_packet.seq <= seq < upper_limit
        else:
            return seq >= sync_packet.seq or seq < upper_limit

    def is_last_packet_allowed(self):
        return self._packets[-1].status != "deny" if len(self._packets) > 0 else True

    def is_last_packet_denied(self):
        return self._packets[-1].status == "deny" if len(self._packets) > 0 else False

    def is_allowed(self):
        """
        True if you have at least a S with (PA or FA) allowed, false otherwise
        """
        has_S_allowed = False
        has_PA_or_FA_allowed = False

        for packet in self._packets:
            if packet.status == "allow":
                if packet.flags == "S":
                    has_S_allowed = True
                elif packet.flags == "PA" or packet.flags == "FA":
                    has_PA_or_FA_allowed = True

            # Early exit if both conditions are met
            if has_S_allowed and has_PA_or_FA_allowed:
                return True

        return has_S_allowed and has_PA_or_FA_allowed

    def is_denied(self):
        """
        True if at least one packet is denied, false otherwise
        """
        return any(
            x.status == "deny" for x in reversed(self._packets) if x.status is not None
        )

    def is_sync_denied(self):
        packets = [x for x in self._packets if x.flags == "S"]
        packet = packets[0] if len(packets) > 0 else None
        return packet.status == "deny" if packet else False

    def is_sync_allowed(self):
        packets = [x for x in self._packets if x.flags == "S"]
        packet = packets[0] if len(packets) > 0 else None
        return packet.status == "allow" if packet else True

    def is_data_denied(self):
        packets = [x for x in self._packets[::-1] if x.flags == "PA"]
        packet = packets[-1] if len(packets) > 0 else None
        return packet.status == "deny" if packet else False

    def is_data_allowed(self):
        packets = [x for x in self._packets[::-1] if x.flags == "PA"]
        packet = packets[-1] if len(packets) > 0 else None
        return packet.status == "allow" if packet else True

    def get_last_packet(self, index=-1, flags=None) -> FirewallPacket | None:
        packets = (
            [x for x in self._packets if x.flags == flags]
            if flags is not None
            else self._packets
        )
        return packets[index] if len(packets) > (index * -1) else FirewallPacket()

    def add_packet(self, packet: FirewallPacket):
        self._packets.append(packet)

    @classmethod
    def from_dict(cls, dict_):
        instance = cls()
        instance.id = dict_.get("request_id")
        instance.previous_id = dict_.get("previous_id")

        packets = dict_.get("packets")
        instance._packets = [FirewallPacket.from_dict(x) for x in packets]

        return instance
