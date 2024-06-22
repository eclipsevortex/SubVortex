import struct
import socket
from subnet.firewall.firewall_packet import FirewallPacket


def checksum(msg):
    if len(msg) % 2 == 1:
        msg += b'\x00'  # Pad to even length if necessary

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


class PacketQueue:
    _result = None

    def __init__(self, src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload, packet_mock):
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
        

    # def accept(self):
    #     self._result = "accept"

    # def is_dropped(self):
    #     return self._result == "drop"
    
    # def is_accepted(self):
    #     return self._result == "accept"


def create_kernel_packet(src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload):
    ip_header = create_ip_header(src_ip, dst_ip)
    tcp_header = create_tcp_header(
        src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload
    )
    return ip_header + tcp_header + payload.encode()


# def send_tcp_request():
#     src_ip = "192.168.1.1"
#     dst_ip = "192.168.1.2"
#     src_port = 12345
#     dst_port = 80

#     # Initial sequence and acknowledgment numbers
#     client_seq = 1000
#     server_seq = 2000
#     client_ack = 0
#     server_ack = client_seq + 1

#     # Step 1: SYN (Client to Server)
#     syn_packet = create_packet(src_ip, dst_ip, src_port, dst_port, client_seq, client_ack, "S", "")
#     packet_callback(syn_packet)

#     # Step 2: SYN-ACK (Server to Client)
#     syn_ack_packet = create_packet(dst_ip, src_ip, dst_port, src_port, server_seq, server_ack, "SA", "")
#     packet_callback(syn_ack_packet)

#     # Step 3: ACK (Client to Server)
#     client_seq += 1
#     client_ack = server_seq + 1
#     ack_packet = create_packet(src_ip, dst_ip, src_port, dst_port, client_seq, client_ack, "A", "")
#     packet_callback(ack_packet)

#     # Step 4: PSH-ACK (Client to Server - Request Data)
#     payload = "GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(dst_ip)
#     psh_ack_packet = create_packet(src_ip, dst_ip, src_port, dst_port, client_seq, client_ack, "PA", payload)
#     packet_callback(psh_ack_packet)

#     # Step 5: ACK (Server to Client)
#     server_ack = client_seq + len(payload)
#     ack_packet = create_packet(dst_ip, src_ip, dst_port, src_port, server_seq, server_ack, "A", "")
#     packet_callback(ack_packet)

#     # Step 6: PSH-ACK (Server to Client - Response Data)
#     payload = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello, World!"
#     psh_ack_packet = create_packet(dst_ip, src_ip, dst_port, src_port, server_seq, server_ack, "PA", payload)
#     packet_callback(psh_ack_packet)

#     # Step 7: ACK (Client to Server)
#     client_ack = server_seq + len(payload)
#     ack_packet = create_packet(src_ip, dst_ip, src_port, dst_port, client_seq, client_ack, "A", "")
#     packet_callback(ack_packet)

#     # Step 8: FIN-ACK (Client to Server)
#     client_seq += len(payload)
#     fin_ack_packet = create_packet(src_ip, dst_ip, src_port, dst_port, client_seq, client_ack, "FA", "")
#     packet_callback(fin_ack_packet)

#     # Step 9: ACK (Server to Client)
#     server_ack = client_seq + 1
#     ack_packet = create_packet(dst_ip, src_ip, dst_port, src_port, server_seq, server_ack, "A", "")
#     packet_callback(ack_packet)

#     # Step 10: FIN-ACK (Server to Client)
#     server_seq += len(payload)
#     fin_ack_packet = create_packet(dst_ip, src_ip, dst_port, src_port, server_seq, server_ack, "FA", "")
#     packet_callback(fin_ack_packet)

#     # Step 11: ACK (Client to Server)
#     client_ack = server_seq + 1
#     ack_packet = create_packet(src_ip, dst_ip, src_port, dst_port, client_seq, client_ack, "A", "")
#     packet_callback(ack_packet)


# def create_kernel_packet(src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload):
#     # IP header fields
#     ip_ihl_ver = (4 << 4) + 5
#     ip_tos = 0
#     ip_tot_len = 20 + 20 + len(payload)  # IP header + TCP header + payload
#     ip_id = 54321
#     ip_frag_off = 0
#     ip_ttl = 64
#     ip_proto = socket.IPPROTO_TCP
#     ip_check = 0
#     ip_saddr = socket.inet_aton(src_ip)
#     ip_daddr = socket.inet_aton(dst_ip)

#     ip_header = struct.pack(
#         "!BBHHHBBH4s4s",
#         ip_ihl_ver,
#         ip_tos,
#         ip_tot_len,
#         ip_id,
#         ip_frag_off,
#         ip_ttl,
#         ip_proto,
#         ip_check,
#         ip_saddr,
#         ip_daddr,
#     )

#     # TCP header fields
#     tcp_offset_res = (5 << 4) + 0
#     tcp_flags = 0
#     if "F" in flags:
#         tcp_flags |= 0x01  # FIN
#     if "S" in flags:
#         tcp_flags |= 0x02  # SYN
#     if "R" in flags:
#         tcp_flags |= 0x04  # RST
#     if "P" in flags:
#         tcp_flags |= 0x08  # PSH
#     if "A" in flags:
#         tcp_flags |= 0x10  # ACK
#     if "U" in flags:
#         tcp_flags |= 0x20  # URG

#     tcp_window = socket.htons(5840)
#     tcp_check = 0
#     tcp_urg_ptr = 0

#     tcp_header = struct.pack(
#         "!HHLLBBHHH",
#         src_port,
#         dst_port,
#         seq,
#         ack,
#         tcp_offset_res,
#         tcp_flags,
#         tcp_window,
#         tcp_check,
#         tcp_urg_ptr,
#     )

#     # Pseudo header fields for checksum calculation
#     psh_saddr = ip_saddr
#     psh_daddr = ip_daddr
#     psh_reserved = 0
#     psh_proto = socket.IPPROTO_TCP
#     psh_tcp_len = struct.pack("!H", len(tcp_header) + len(payload))

#     psh = (
#         psh_saddr
#         + psh_daddr
#         + struct.pack("!BBH", psh_reserved, psh_proto, len(tcp_header) + len(payload))
#     )
#     psh = psh + tcp_header + payload.encode()

#     tcp_check = checksum(psh)

#     # Recreate the TCP header with the correct checksum
#     tcp_header = (
#         struct.pack(
#             "!HHLLBBH",
#             src_port,
#             dst_port,
#             seq,
#             ack,
#             tcp_offset_res,
#             tcp_flags,
#             tcp_window,
#         )
#         + struct.pack("H", tcp_check)
#         + struct.pack("!H", tcp_urg_ptr)
#     )

#     packet = ip_header + tcp_header + payload.encode()

#     return packet


def create_packet(src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload, packet_mock):
    packet = PacketQueue(src_ip, dst_ip, src_port, dst_port, seq, ack, flags, payload, packet_mock)
    return FirewallPacket(packet)
