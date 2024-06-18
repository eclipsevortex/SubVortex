import os
import copy
import json
import time
import logging
import threading
import bittensor as bt
from typing import List
from collections import defaultdict
from scapy.all import sniff, TCP, UDP, IP, Raw, Packet

from subnet.shared.encoder import EnumEncoder
from subnet.firewall.firewall_model import (
    FirewallTool,
    create_rule,
    Rule,
    AllowRule,
    DenyRule,
    RuleType,
    DetectDoSRule,
    DetectDDoSRule,
)

# Disalbe scapy logging
logging.getLogger("scapy.runtime").setLevel(logging.CRITICAL)


# User can define a rule wih ip, port (with or without protocol) or ip/port (with or without protocol)
class Firewall(threading.Thread):
    def __init__(
        self,
        tool: FirewallTool,
        interface: str,
        port: int = 8091,
        rules=[],
    ):
        super().__init__(daemon=True)

        self._whitelist_lock = threading.Lock()
        self._blacklist_lock = threading.Lock()
        self._specifications_lock = threading.Lock()
        self.stop_flag = threading.Event()
        self.packet_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.packet_timestamps = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        self.tool = tool
        self.port = port
        self.interface = interface
        self.ips_blocked = []
        self.whitelist_ips = []
        self.blacklist_ips = []
        self.specifications = {}

        self.rules = [create_rule(x) for x in rules]

    def start(self):
        super().start()
        bt.logging.debug(f"Firewall started")

    def stop(self):
        self.stop_flag.set()
        super().join()
        bt.logging.debug(f"Firewall stopped")

    def is_whitelisted(self, ip: str):
        with self._whitelist_lock:
            return ip in self.whitelist_ips

    def is_blacklisted(self, ip: str):
        with self._blacklist_lock:
            return ip in self.blacklist_ips

    def update_whitelist(self, whitelist_ips=[]):
        previous_whitelist_ips = []
        with self._whitelist_lock:
            previous_whitelist_ips = list(self.whitelist_ips)
            self.whitelist_ips = list(whitelist_ips)

        # Remove old whitelist ips
        ips_to_remove = list(set(previous_whitelist_ips) - set(self.whitelist_ips))
        for ip in ips_to_remove:
            self.tool.remove_rule(ip, self.port, "tcp")

        # Add whitelist ips
        for ip in self.whitelist_ips:
            success = self.tool.create_allow_rule(ip=ip, port=self.port, protocol="tcp")
            if success:
                self.rules.append(AllowRule(ip=ip))

    def update_blacklist(self, blacklist_ips=[]):
        previous_blacklist_ips = []
        with self._blacklist_lock:
            previous_blacklist_ips = list(self.blacklist_ips)
            self.blacklist_ips = list(blacklist_ips)

        # Remove old whitelist ips
        ips_to_remove = list(set(previous_blacklist_ips) - set(self.blacklist_ips))
        for ip in ips_to_remove:
            self.tool.remove_rule(ip, self.port, "tcp")

        # Add blacklist ips
        for ip in self.blacklist_ips:
            success = self.tool.create_deny_rule(ip=ip, port=self.port, protocol="tcp")
            if success:
                self.rules.append(DenyRule(ip=ip))

    def update_specifications(self, specifications):
        with self._specifications_lock:
            self.specifications = copy.deepcopy(specifications)

    def update_versions(version):
        return 225

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
        self.tool.create_deny_rule(ip=ip, port=port, protocol=protocol)

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
        self.tool.remove_rule(ip=ip, port=port, protocol=protocol, allow=False)

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

    def check_specifications(self, payload):
        """
        True if the packet is conformed with the expected specifications (neuron synapse, version, etc), false otherwise
        """
        content = payload.decode("utf-8")

        # Split the HTTP request data into lines
        lines = content.split("\n")

        # Set default value
        name = None
        neuron_version = 0

        # Get the value for each expected property
        for line in lines:
            if "name" in line:
                # Split the line to get the value
                _, value = line.split(":", 1)
                # Strip any extra whitespace and print the value
                name = value.strip()

            if "bt_header_dendrite_neuron_version" in line:
                # Split the line to get the value
                _, value = line.split(":", 1)
                # Strip any extra whitespace and print the value
                neuron_version = int(value.strip()) if value else 0

        specifications = {}
        with self._specifications_lock:
            specifications = copy.deepcopy(self.specifications)

        # Check if the packet matches an expected synapses
        synapses = specifications.get("synapses") or []
        if len(synapses) > 0 and name.lower() not in synapses:
            return (
                False,
                f"Synapse name '{name}' not found",
            )

        # Check if the neuron version is greater stricly than the one required
        neuron_version_required = int(specifications.get("neuron_version") or 0)
        if neuron_version < neuron_version_required:
            return (
                False,
                f"Neuron version {neuron_version} is outdated; version {225} is required.",
            )

        return (True, None)

    def get_rule(self, rules: List[Rule], type: RuleType, ip, port, protocol):
        filtered_rules = [r for r in rules if r.rule_type == type]

        # Ip/Port rule
        rule = next(
            (
                r
                for r in filtered_rules
                if r.ip == ip and r.port == port and r.protocol == protocol
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
        rules = [r for r in self.rules if r.ip == ip_src or r.port == port_dest]

        # Get the current time
        current_time = time.time()

        # Add the new time for ip/port
        self.packet_counts[ip_src][port_dest][protocol] += 1
        self.packet_timestamps[ip_src][port_dest][protocol].append(current_time)

        # Check if a allow rule exist
        allow_rule = self.get_rule(
            rules=rules,
            type=RuleType.ALLOW,
            ip=ip_src,
            port=port_dest,
            protocol=protocol,
        )

        # Check if a allow rule exist
        deny_rule = self.get_rule(
            rules=rules,
            type=RuleType.DENY,
            ip=ip_src,
            port=port_dest,
            protocol=protocol,
        )

        # Check request specs
        specs_success, specs_reason = self.check_specifications(packet[Raw].load)

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
            if dos_rule and specs_success
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
            if ddos_rule and specs_success
            else (False, None)
        )

        has_detection_rule = dos_rule or ddos_rule
        attack_detected = dos_detected or ddos_detected or not specs_success
        attack_type = (
            (dos_detected and RuleType.DETECT_DOS)
            or (ddos_detected and RuleType.DETECT_DDOS)
            or (not specs_success and RuleType.SPECIFICATION)
        )
        attack_reason = dos_reason or ddos_reason or specs_reason

        if attack_detected or (not has_detection_rule and not allow_rule):
            if deny_rule:
                return

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
                self.tool.create_allow_rule(ip=ip, port=port, protocol=protocol)
            else:
                self.tool.create_deny_rule(ip=ip, port=port, protocol=protocol)

        # Start sniffing with the filter
        sniff(
            iface=self.interface,
            prn=self.packet_callback,
            store=False,
            stop_filter=self.stop_flag.set(),
        )
