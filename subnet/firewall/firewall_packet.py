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
import json
import struct
import socket
import bittensor as bt

from subnet.shared.type import get_key_from_value, get_enum_name_from_value
from subnet.shared.encoder import encodeBase64, decodeBase64
from subnet.firewall.firewall_model import RuleType
from subnet.firewall.firewall_utils import extract_and_transform_headers, get

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


class FirewallHeaders:
    def __init__(self):
        self.synapse_name = None
        self.axon_ip = None
        self.axon_port = None
        self.axon_hotkey = None
        self.dendrite_ip = None
        self.dendrite_port = None
        self.dendrite_version = None
        self.dendrite_neuron_version = None
        self.dendrite_nonce = None
        self.dendrite_uuid = None
        self.dendrite_hotkey = None
        self.dendrite_signature = None
        self.computed_body_hash = None

    @classmethod
    def from_payload(cls, payload):
        # Decode the payload
        content = ""
        try:
            content = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        except:
            pass

        if payload is None or content == "":
            return FirewallHeaders.from_dict({})

        # The content is a json
        try:
            data = json.loads(content)
            return FirewallHeaders.from_dict(data)
        except:
            pass

        # The content is a string
        try:
            # Extract the header and body from the content
            headers_content, body_content = content.split("\r\n\r\n", 1)

            if "Content-Type: application/json" in headers_content:
                data = json.loads(body_content)
            else:
                data = extract_and_transform_headers(content)
        except ValueError as e:
            data = extract_and_transform_headers(content)

        return FirewallHeaders.from_dict(data)

    @classmethod
    def from_dict(cls, dict_):
        instance = cls()
        instance.synapse_name = get(dict_, "name")
        instance.axon_ip = get(dict_, "axon_ip") or get(dict_, "axon.ip")
        instance.axon_port = get(dict_, "axon_port") or get(dict_, "axon.port")
        instance.axon_hotkey = get(dict_, "axon_hotkey") or get(dict_, "axon.hotkey")
        instance.dendrite_ip = get(dict_, "dendrite_ip") or get(dict_, "dendrite.ip")
        instance.dendrite_port = get(dict_, "dendrite_port") or get(
            dict_, "dendrite.port"
        )
        instance.dendrite_version = get(dict_, "dendrite_version") or get(
            dict_, "dendrite.version"
        )
        instance.dendrite_neuron_version = get(dict_, "dendrite_neuron_version") or get(
            dict_, "dendrite.neuron_version"
        )
        instance.dendrite_nonce = get(dict_, "dendrite_nonce") or get(
            dict_, "dendrite.nonce"
        )
        instance.dendrite_uuid = get(dict_, "dendrite_uuid") or get(
            dict_, "dendrite.uuid"
        )
        instance.dendrite_hotkey = get(dict_, "dendrite_hotkey") or get(
            dict_, "dendrite.hotkey"
        )
        instance.dendrite_signature = get(dict_, "dendrite_signature") or get(
            dict_, "dendrite.signature"
        )
        instance.computed_body_hash = get(dict_, "computed_body_hash")
        return instance


class FirewallPacket:
    def __init__(self):
        self.queue_num = 1
        self._current_time = None
        self.process_time = None
        self._packet = None
        self._raw_packet = None
        self.notified = False
        self.max_time = 0

        # Properties for final decision (drop or accept)
        self.status = None
        self.type = None
        self.reason = None

        # Initialize TCP fields to None
        self._src_ip = None
        self._src_port = None
        self._dst_ip = None
        self._dst_port = None
        self._ip_protocol = None
        self._seq = 0
        self._ack = 0
        self._flags = None
        self._payload = None
        self._headers: FirewallHeaders = None

    @property
    def internal_id(self):
        return f"{self.sip}:{self.dport}:{self.seq}:{self.ack}:{self.flags}"

    @property
    def id(self):
        return f"{self.sip}:{self.dport}:{self.protocol}"

    @property
    def current_time(self):
        return self._current_time

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
        return self._flags

    @property
    def seq(self):
        return self._seq

    @property
    def ack(self):
        return self._ack

    @property
    def payload(self):
        return self._payload

    @property
    def headers(self):
        return self._headers

    def accept(self):
        self.status = "allow"
        self.type = RuleType.ALLOW

    def drop(self, type, reason):
        self.status = "deny"
        self.type = type or RuleType.DENY
        self.reason = reason or "Deny ip"

    def commit(self):
        try:
            if self.status == "allow":
                self._packet.accept()
            elif self.status == "deny":
                self._packet.drop()
        except Exception as err:
            bt.logging.error(err)
            return False

    def to_dict(self):
        return {
            "current_time": self.current_time,
            "process_time": self.process_time,
            "queue_num": self.queue_num,
            "notified": self.notified,
            "sip": self.sip,
            "protocol": self.protocol,
            "dip": self.dip,
            "dport": self.dport,
            "sport": self.sport,
            "flags": self.flags,
            "seq": self.seq,
            "ack": self.ack,
            "payload": encodeBase64(self.payload),
            "status": self.status,
            "type": self.type.value if self.type else "",
            "reason": self.reason,
            "max_time": self.max_time,
            "synapse": self.headers.synapse_name,
            "axon": {
                "ip": self._headers.axon_ip,
                "port": self._headers.axon_port,
                "hotkey": self._headers.axon_hotkey,
            },
            "dendrite": {
                "ip": self._headers.dendrite_ip,
                "port": self._headers.dendrite_port,
                "hotkey": self._headers.dendrite_hotkey,
                "signature": self._headers.dendrite_signature,
                "nonce": self._headers.dendrite_nonce,
                "uuid": self._headers.dendrite_uuid,
                "version": self._headers.dendrite_version,
                "neuron_version": self._headers.dendrite_neuron_version,
            },
        }

    @classmethod
    def from_dict(cls, dict_):
        instance = cls()
        instance._current_time = dict_.get("current_time")
        instance._src_ip = dict_.get("sip")
        instance._ip_protocol = get_key_from_value(dict_.get("protocol"), PROTOCOLS)
        instance._dst_ip = dict_.get("dip")
        instance._dst_port = int(dict_.get("dport", 0))
        instance._src_port = int(dict_.get("sport", 0))
        instance.max_time = int(dict_.get("max_time", 0))
        instance._flags = dict_.get("flags")
        instance._seq = int(dict_.get("seq", 0))
        instance._ack = int(dict_.get("ack", 0))
        payload = dict_.get("payload")
        instance._payload = decodeBase64(payload) if payload else None
        instance._headers = FirewallHeaders.from_payload(instance._payload)
        instance.status = dict_.get("status")
        instance.type = get_enum_name_from_value(dict_.get("type"), RuleType)
        instance.reason = dict_.get("reason")
        instance.queue_num = int(dict_.get("queue_num", 1))
        return instance

    @classmethod
    def from_packet(cls, packet, current_time, queue_num=1):
        instance = cls()
        instance.queue_num = queue_num
        instance._current_time = current_time
        instance._packet = packet
        instance._raw_packet = packet.get_payload()

        # Parse IP header (first 20 bytes)
        ip_header = instance._raw_packet[:20]
        ip_data = struct.unpack("!BBHHHBBH4s4s", ip_header)
        instance._ip_protocol = ip_data[6]
        instance._src_ip = socket.inet_ntoa(ip_data[8])
        instance._dst_ip = socket.inet_ntoa(ip_data[9])

        # Parse TCP header if the protocol is TCP (protocol number 6)
        if instance._ip_protocol == 6:
            ip_header_length = (ip_data[0] & 0x0F) * 4
            tcp_header_offset = ip_header_length
            tcp_header = instance._raw_packet[
                tcp_header_offset : tcp_header_offset + 20
            ]
            tcp_data = struct.unpack("!HHLLBBHHH", tcp_header)
            tcp_header_length = ((tcp_data[4] >> 4) & 0xF) * 4
            instance._src_port = tcp_data[0]
            instance._dst_port = tcp_data[1]
            instance._seq = tcp_data[2]
            instance._ack = tcp_data[3]
            instance._flags = "".join(
                label
                for bit, label in TCP_FLAG_LABELS.items()
                if tcp_data[5] & 0x3F & bit
            )

            # Calculate payload offset and extract payload
            payload_offset = tcp_header_offset + tcp_header_length
            instance._payload = instance._raw_packet[payload_offset:]
            instance._headers = FirewallHeaders.from_payload(instance._payload)

        return instance
