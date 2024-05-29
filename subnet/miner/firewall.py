import os
import json
import time
import logging
import threading
import bittensor as bt
from typing import List
from collections import defaultdict
from scapy.all import sniff, TCP, UDP, IP, Packet

from subnet.shared.encoder import EnumEncoder
from subnet.miner.firewall_models import create_rule, Rule, RuleType, DetectDoSRule, DetectDDoSRule
from subnet.miner.iptables import (
    deny_traffic_from_ip,
    deny_traffic_on_port,
    deny_traffic_from_ip_and_port,
    allow_traffic_from_ip,
    allow_traffic_on_port,
    allow_traffic_from_ip_and_port,
    remove_deny_traffic_from_ip_and_port,
)

# Disalbe scapy logging
logging.getLogger("scapy.runtime").setLevel(logging.CRITICAL)


# User can define a rule wih ip, port (with or without protocol) or ip/port (with or without protocol)
class Firewall(threading.Thread):
    def __init__(
        self,
        interface: str,
        rules=[],
    ):
        super().__init__(daemon=True)

        self.stop_flag = threading.Event()
        self.packet_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.packet_timestamps = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        self.interface = interface
        self.ips_blocked = []

        self.rules = [create_rule(x) for x in rules]

    def start(self):
        super().start()
        bt.logging.debug(f"Firewall started")

    def stop(self):
        self.stop_flag.set()
        super().join()
        bt.logging.debug(f"Firewall stopped")

    def block_ip(self, ip, port, protocol, type, reason):
        ip_blocked = next(
            (
                x
                for x in self.ips_blocked
                if x["ip"] == ip and x["port"] == port and x["protocol"] == protocol
            ),
            None,
        )
        if ip_blocked:
            return

        # Update the ip tables
        deny_traffic_from_ip_and_port(ip, port, protocol)

        # Update the block ips
        ip_blocked = {
            "ip": ip,
            "port": port,
            "protocol": protocol,
            "type": type,
            "reason": reason,
        }
        self.ips_blocked.append(ip_blocked)

        # Update the local file
        with open("ips_blocked.json", "w") as file:
            file.write(json.dumps(self.ips_blocked, cls=EnumEncoder))

        bt.logging.warning(f"Blocking {protocol.upper()} {ip}/{port}: {reason}")

    def unblock_ip(self, ip, port, protocol):
        ip_blocked = next(
            (
                x
                for x in self.ips_blocked
                if x["ip"] == ip and x["port"] == port and x["protocol"] == protocol
            ),
            None,
        )
        if not ip_blocked:
            return

        # Update the ip tables
        remove_deny_traffic_from_ip_and_port(ip, port, protocol)

        # Update the block ips
        self.ips_blocked = [
            x
            for x in self.ips_blocked
            if x["ip"] != ip or x["port"] != port or x["protocol"] != protocol
        ]

        # Update the local file
        with open("ips_blocked.json", "w") as file:
            file.write(json.dumps(self.ips_blocked, cls=EnumEncoder))

        bt.logging.warning(f"Unblocking {protocol.upper()} {ip}/{port}")

    def detect_dos(self, ip, port, protocol, rule: DetectDoSRule, current_time):
        """
        Detect Denial of Service attack which is an attack from a single source that overwhelms a target with requests,
        """
        recent_packets = [
            t
            for t in self.packet_timestamps[ip][port][protocol]
            if current_time - t < rule.time_window
        ]
        self.packet_timestamps[ip][port][protocol] = recent_packets

        if len(recent_packets) > rule.packet_threshold:
            return (
                True,
                f"DoS attack detected: {len(recent_packets)} packets in {rule.time_window} seconds",
            )

        return (False, None)

    def detect_ddos(self, port, rule: DetectDDoSRule, current_time):
        """
        Detect Distributed Denial of Service which is an attack from multiple sources that overwhelms a target with requests,
        """
        all_timestamps = [
            timestamp
            for ports in self.packet_timestamps.values()
            for times in ports[port].values()
            for timestamp in times
        ]

        recent_timestamps = [
            t for t in all_timestamps if current_time - t < rule.time_window
        ]

        if len(recent_timestamps) > rule.packet_threshold:
            return (
                True,
                f"DDoS attack detected: {len(recent_timestamps)} packets in {rule.time_window} seconds",
            )

        return (False, None)

    def get_rule(self, rules: List[Rule], type: RuleType, ip, port, protocol):
        filtered_rules = [r for r in rules if r.rule_type == type]

        # Ip/Port rule
        rule = next(
            (
                r
                for r in filtered_rules
                if r.ip == ip
                and r.port == port
                and r.protocol == protocol
            ),
            None,
        )

        # Ip rule
        rule = rule or next(
            (
                r
                for r in filtered_rules
                if ip is not None
                and r.ip == ip
                and r.port is None
                and r.protocol is None
            ),
            None,
        )

        # Port rule
        rule = rule or next(
            (
                r
                for r in filtered_rules
                if port is not None
                and r.port == port
                and r.protocol == protocol
                and r.ip is None
            ),
            None,
        )

        return rule

    def packet_callback(self, packet: Packet):
        # Get the protocol
        protocol = "tcp" if TCP in packet else "udp" if UDP in packet else None

        # Get the destination port
        port_dest = (
            packet[TCP].dport
            if TCP in packet
            else packet[UDP].dport if UDP in packet else None
        )

        # Get the source ip
        ip_src = packet[IP].src if IP in packet else None
        if ip_src is None:
            return

        # Get all rules related to the ip/port
        rules = [
            r for r in self.rules if r.ip == ip_src or r.port == port_dest
        ]

        # Get the current time
        current_time = time.time()

        # Add the new time for ip/port
        self.packet_counts[ip_src][port_dest][protocol] += 1
        self.packet_timestamps[ip_src][port_dest][protocol].append(current_time)

        # Check if a allow rule exist
        allow_rule = self.get_rule(
            rules=rules, type=RuleType.ALLOW, ip=ip_src, port=port_dest, protocol=protocol
        )

        # Check if a DoS rule exist
        dos_rule = self.get_rule(
            rules=rules,
            type=RuleType.DETECT_DOS,
            ip=ip_src,
            port=port_dest,
            protocol=protocol,
        )
        dos_detected, dos_reason = (
            self.detect_dos(
                ip_src,
                port_dest,
                protocol,
                dos_rule,
                current_time,
            )
            if dos_rule
            else (False, None)
        )

        # Check if a DDoS rule exist
        ddos_rule = self.get_rule(
            rules=rules,
            type=RuleType.DETECT_DDOS,
            ip=ip_src,
            port=port_dest,
            protocol=protocol,
        )
        ddos_detected, ddos_reason = (
            self.detect_ddos(
                port_dest,
                ddos_rule,
                current_time,
            )
            if ddos_rule
            else (False, None)
        )

        has_detection_rule = dos_rule or ddos_rule
        attack_detected = dos_detected or ddos_detected
        attack_type = (dos_detected and RuleType.DETECT_DOS) or (ddos_detected and RuleType.DETECT_DDOS)
        attack_reason = dos_reason or ddos_reason

        if attack_detected or (not has_detection_rule and not allow_rule):
            self.block_ip(
                ip=ip_src,
                port=port_dest,
                protocol=protocol,
                type=attack_type or RuleType.DENY,
                reason=attack_reason or "Deny ip",
            )
            return

        # Unblock the ip/port
        self.unblock_ip(ip_src, port_dest, protocol)

    def run(self):
        # Reload the previous ips blocked
        bt.logging.debug("Loading blocked ips")
        if os.path.exists("ips_blocked.json"):
            with open("ips_blocked.json", "r") as file:
                self.ips_blocked = json.load(file) or []

        bt.logging.debug(f"Applying allow/deny rules")
        for rule in self.rules:
            if rule.rule_type not in [RuleType.ALLOW, RuleType.DENY]:
                continue

            ip = rule.ip
            port = rule.port
            protocol = rule.protocol
            type = rule.rule_type

            if type == RuleType.ALLOW:
                if ip and port:
                    allow_traffic_from_ip_and_port(ip, port, protocol)
                elif ip:
                    allow_traffic_from_ip(ip)
                elif port:
                    allow_traffic_on_port(port, protocol)
            else:
                if ip and port:
                    deny_traffic_from_ip_and_port(ip, port, protocol)
                elif ip:
                    deny_traffic_from_ip(ip)
                elif port:
                    deny_traffic_on_port(port, protocol)

        # Start sniffing with the filter
        sniff(
            iface=self.interface,
            prn=self.packet_callback,
            store=False,
            stop_filter=self.stop_flag.set(),
        )
