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

import struct
import socket

PROTOCOLS = {
    1: "icmp",
    6: "tcp",
    17: "udp",
}

TCP_FLAG_LABELS = {
    0x01: "F",  # FIN
    0x02: "S",  # SYN
    0x04: "R",  # RST
    0x08: "P",  # PSH
    0x10: "A",  # ACK
    0x20: "U",  # URG
    0x40: "E",  # ECE
    0x80: "C",  # CWR
}


class FirewallPacket:
    def __init__(self, packet, queue_num = 1):
        self.queue_num = queue_num
        self._packet = packet
        self._raw_packet = packet.get_payload()

        # Parse IP header (first 20 bytes)
        ip_header = self._raw_packet[:20]
        ip_data = struct.unpack("!BBHHHBBH4s4s", ip_header)
        self._ip_protocol = ip_data[6]
        self._src_ip = socket.inet_ntoa(ip_data[8])
        self._dst_ip = socket.inet_ntoa(ip_data[9])

        # Initialize TCP fields to None
        self._src_port = None
        self._dst_port = None
        self._seq = None
        self._ack = None
        self._flags = None
        self._payload = None

        # Parse TCP header if the protocol is TCP (protocol number 6)
        if self._ip_protocol == 6:
            ip_header_length = (ip_data[0] & 0x0F) * 4
            tcp_header_offset = ip_header_length
            tcp_header = self._raw_packet[tcp_header_offset : tcp_header_offset + 20]
            tcp_data = struct.unpack("!HHLLBBHHH", tcp_header)
            tcp_header_length = ((tcp_data[4] >> 4) & 0xF) * 4
            self._src_port = tcp_data[0]
            self._dst_port = tcp_data[1]
            self._seq = tcp_data[2]
            self._ack = tcp_data[3]
            self._flags = tcp_data[5] & 0x3F

            # Calculate payload offset and extract payload
            payload_offset = tcp_header_offset + tcp_header_length
            self._payload = self._raw_packet[payload_offset:]

    @property
    def internal_id(self):
        return f"{self.sip}:{self.dport}:{self.seq}:{self.ack}"

    @property
    def id(self):
        return f"{self.sip}:{self.dport}"

    @property
    def sip(self):
        return self._src_ip

    @property
    def protocol(self):
        return PROTOCOLS.get(self._ip_protocol, None)

    @property
    def dip(self):
        return self._dst_ip

    @property
    def dport(self):
        return self._dst_port

    @property
    def sport(self):
        return self._src_port

    @property
    def flags(self):
        # Convert numeric flags to string representation
        flag_str = "".join(
            label for bit, label in TCP_FLAG_LABELS.items() if self._flags & bit
        )
        return flag_str if flag_str else None

    @property
    def seq(self):
        return self._seq

    @property
    def ack(self):
        return self._ack

    @property
    def payload(self):
        return self._payload
    
    def accept(self):
        try:
            self._packet.accept()
            return True
        except: 
            return False

    def drop(self):
        try:
            self._packet.drop()
            return True
        except: 
            return False
