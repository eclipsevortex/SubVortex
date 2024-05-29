import struct
import socket
from subnet.firewall.firewall_packet import FirewallPacket


def checksum(msg):
    if len(msg) % 2 == 1:
        msg += b"\x00"  # Pad to even length if necessary

    s = 0
    for i in range(0, len(msg), 2):
        w = (msg[i] << 8) + (msg[i + 1])
        s = s + w

    s = (s >> 16) + (s & 0xFFFF)
    s = ~s & 0xFFFF
    return s


def create_ip_header(src_ip, dst_ip):
    ip_ihl_ver = (4 << 4) + 5
    ip_tos = 0
    ip_tot_len = 20 + 20  # IP header + TCP header
    ip_id = 54321
    ip_frag_off = 0
    ip_ttl = 64
    ip_proto = socket.IPPROTO_TCP
    ip_check = 0
    ip_saddr = socket.inet_aton(src_ip)
    ip_daddr = socket.inet_aton(dst_ip)

    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        ip_ihl_ver,
        ip_tos,
        ip_tot_len,
        ip_id,
        ip_frag_off,
        ip_ttl,
        ip_proto,
        ip_check,
        ip_saddr,
        ip_daddr,
    )
    return ip_header


def create_tcp_header(src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload):
    tcp_offset_res = (5 << 4) + 0
    tcp_flags = 0
    if "F" in flags:
        tcp_flags |= 0x01  # FIN
    if "S" in flags:
        tcp_flags |= 0x02  # SYN
    if "R" in flags:
        tcp_flags |= 0x04  # RST
    if "P" in flags:
        tcp_flags |= 0x08  # PSH
    if "A" in flags:
        tcp_flags |= 0x10  # ACK
    if "U" in flags:
        tcp_flags |= 0x20  # URG

    tcp_window = socket.htons(5840)
    tcp_check = 0
    tcp_urg_ptr = 0

    tcp_header = struct.pack(
        "!HHLLBBHHH",
        src_port,
        dst_port,
        seq,
        ack,
        tcp_offset_res,
        tcp_flags,
        tcp_window,
        tcp_check,
        tcp_urg_ptr,
    )

    # Pseudo header fields for checksum calculation
    psh_saddr = socket.inet_aton(src_ip)
    psh_daddr = socket.inet_aton(dst_ip)
    psh_reserved = 0
    psh_proto = socket.IPPROTO_TCP
    psh_tcp_len = struct.pack("!H", len(tcp_header) + len(payload))

    psh = (
        psh_saddr
        + psh_daddr
        + struct.pack("!BBH", psh_reserved, psh_proto, len(tcp_header) + len(payload))
    )
    psh = psh + tcp_header + payload.encode()

    tcp_check = checksum(psh)

    # Recreate the TCP header with the correct checksum
    tcp_header = (
        struct.pack(
            "!HHLLBBH",
            src_port,
            dst_port,
            seq,
            ack,
            tcp_offset_res,
            tcp_flags,
            tcp_window,
        )
        + struct.pack("H", tcp_check)
        + struct.pack("!H", tcp_urg_ptr)
    )

    return tcp_header


class PacketMock:
    _result = None

    def __init__(
        self, src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload, packet_mock
    ):
        self.ip_header = create_ip_header(src_ip, dst_ip)
        self.tcp_header = create_tcp_header(
            src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload
        )
        self.payload = payload
        self.packet_mock = packet_mock

    def get_payload(self):
        return self.ip_header + self.tcp_header + self.payload.encode()

    def drop(self):
        self.packet_mock.drop()

    def accept(self):
        self.packet_mock.accept()


def create_kernel_packet(src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload):
    ip_header = create_ip_header(src_ip, dst_ip)
    tcp_header = create_tcp_header(
        src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload
    )
    return ip_header + tcp_header + payload.encode()


def create_packet(
    src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload, packet_mock, mock_time
):
    packet = PacketMock(
        src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload, packet_mock
    )
    return FirewallPacket.from_packet(
        packet=packet, current_time=mock_time.return_value
    )
