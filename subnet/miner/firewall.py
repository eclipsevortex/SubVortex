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
        self.whitelist_hotkeys = []
        self.blacklist_hotkeys = []
        self.specifications = {}

        self.rules = [create_rule(x) for x in rules]

    def start(self):
        super().start()
        bt.logging.debug(f"Firewall started")

    def stop(self):
        self.stop_flag.set()
        super().join()
        bt.logging.debug(f"Firewall stopped")

    def is_whitelisted(self, hotkey: str):
        is_whitelisted = False
        with self._whitelist_lock:
            is_whitelisted = hotkey in self.whitelist_hotkeys

        if is_whitelisted:
            return (True, None, None)

        return (False, RuleType.DENY, f"Hotkey '{hotkey}' is not whitelisted")

    def is_blacklisted(self, hotkey: str):
        is_blacklisted = False
        with self._blacklist_lock:
            is_blacklisted = hotkey in self.blacklist_hotkeys

        if is_blacklisted:
            return (True, RuleType.DENY, f"Hotkey '{hotkey}' is blacklisted")

        return (False, None, None)

    def is_unknown_synapse(self, name: str):
        """
        True if the synapse is an allowed one, false otherwise
        """
        synapses = self.get_specification("synapses") or []
        if len(synapses) > 0 and name.lower() not in synapses:
            return (True, RuleType.DENY, f"Synapse name '{name}' not found")

        return (False, None, None)

    def is_old_neuron_version(self, version: int):
        """
        True if the neuron version is greater stricly than the one required, false otherwise
        """
        version_required = int(self.get_specification("neuron_version") or 0)
        if version < version_required:
            return (
                True,
                RuleType.DENY,
                f"Neuron version {version} is outdated; version {225} is required.",
            )

        return (False, None, None)

    def update_whitelist(self, whitelist_hotkeys=[]):
        with self._whitelist_lock:
            self.whitelist_hotkeys = list(whitelist_hotkeys)

    def update_blacklist(self, blacklist_hotkeys=[]):
        with self._blacklist_lock:
            self.blacklist_hotkeys = list(blacklist_hotkeys)

    def update_specifications(self, specifications):
        with self._specifications_lock:
            self.specifications = copy.deepcopy(specifications)

    def get_specification(self, name: str):
        with self._specifications_lock:
            specifications = copy.deepcopy(self.specifications)
            return specifications.get(name)

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
                RuleType.DETECT_DOS,
                f"DoS attack detected: {len(recent_packets)} packets in {rule.time_window} seconds",
            )

        return (False, None, None)

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
                RuleType.DETECT_DDOS,
                f"DDoS attack detected: {len(recent_timestamps)} packets in {rule.time_window} seconds",
            )

        return (False, None, None)

    def extract_infos(self, payload):
        """
        Extract information we want to check to determinate if we allow or not the packet
        """
        try:
            content = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        except Exception:
            return (
                False,
                f"Synapse unknown",
            )

        # Split the HTTP request data into lines
        lines = content.split("\n")

        # Set default value
        name = ""
        neuron_version = 0
        hotkey = None

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

            if "bt_header_dendrite_hotkey" in line:
                # Split the line to get the value
                _, value = line.split(":", 1)
                # Strip any extra whitespace and print the value
                hotkey = value.strip()

        return (name, neuron_version, hotkey)

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
        match_allow_rule = self.get_rule(
            rules=rules,
            type=RuleType.ALLOW,
            ip=ip_src,
            port=port_dest,
            protocol=protocol,
        ) is not None

        # Initialise variables
        must_deny = False
        must_allow = match_allow_rule
        rule_type = None
        reason = None

        # Extract data from packet content
        name, neuron_version, hotkey = self.extract_infos(
            packet[Raw].load if Raw in packet else ("", None, None)
        )

        # Check if the hotkey is blacklisted
        must_deny, rule_type, reason = (
            self.is_blacklisted(hotkey)
            if not must_deny
            else (must_deny, rule_type, reason)
        )

        # Check if the packet matches an expected synapses
        must_deny, rule_type, reason = (
            self.is_unknown_synapse(name)
            if not must_deny
            else (must_deny, rule_type, reason)
        )

        # Check if the neuron version is greater stricly than the one required
        must_deny, rule_type, reason = (
            self.is_old_neuron_version(neuron_version)
            if not must_deny
            else (must_deny, rule_type, reason)
        )

        # Check if a DoS attack is found
        dos_rule = self.get_rule(
            rules=rules,
            type=RuleType.DETECT_DOS,
            ip=ip_src,
            port=port_dest,
            protocol=protocol,
        )
        must_deny, rule_type, reason = (
            self.detect_dos(
                ip_src,
                port_dest,
                protocol,
                dos_rule,
                current_time,
            )
            if dos_rule and not must_deny
            else (must_deny, rule_type, reason)
        )

        # Check if a DDoS attack is found
        ddos_rule = self.get_rule(
            rules=rules,
            type=RuleType.DETECT_DDOS,
            ip=ip_src,
            port=port_dest,
            protocol=protocol,
        )
        must_deny, rule_type, reason = (
            self.detect_ddos(
                port_dest,
                ddos_rule,
                current_time,
            )
            if ddos_rule and not must_deny
            else (must_deny, rule_type, reason)
        )

        # By default all traffic is denied, so if there is not allow rule 
        # we check if the hotkey is whitelisted
        if not must_allow: # and not (dos_rule or ddos_rule):
            # One of the detection has been used, so we use the default behaviour of a detection rule
            # which is allowing the traffic except if detecting something abnormal
            must_allow = dos_rule or ddos_rule

            # Check if the hotkey is whitelisted
            must_allow, rule_type, reason = (
                self.is_whitelisted(hotkey)
                if not must_deny and not must_allow
                else (must_allow, rule_type, reason)
            )

        # if attack_detected or (not has_detection_rule and not must_allow):
        if must_deny or not must_allow:
            self.block_ip(
                ip=ip_src,
                port=port_dest,
                protocol=protocol,
                type=rule_type,
                reason=reason or "Deny ip",
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
