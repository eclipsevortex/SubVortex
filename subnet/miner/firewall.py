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
import copy
import time
import threading
import traceback
import numpy as np
import bittensor.utils.btlogging as btul
from datetime import datetime
from typing import List
from collections import defaultdict
from substrateinterface import Keypair

from subnet.shared.file import load_njson_file
from subnet.sse.sse_server import SSEServer
from subnet.file.file_local_monitor import FileLocalMonitor
from subnet.firewall.firewall_packet import FirewallPacket
from subnet.firewall.firewall_request import FirewallRequest
from subnet.firewall.firewall_observer import FirewallObserver
from subnet.firewall.firewall_monitor import FirewallMonitor
from subnet.firewall.firewall_tool import FirewallTool
from subnet.firewall.firewall_utils import clean_sources
from subnet.firewall.firewall_model import (
    create_rule,
    Rule,
    RuleType,
    DetectDoSRule,
    DetectDDoSRule,
)
from subnet.firewall.firewall_constants import (
    FIREWALL_LOGGING_NAME,
    FIREWALL_ATTEMPTS,
    FIREWALL_SLEEP,
    FIREWALL_REQUEST_HISTORY_DURATION,
)


class Firewall(threading.Thread):
    def __init__(
        self,
        tool: FirewallTool,
        observer: FirewallObserver,
        sse: SSEServer,
        interface: str,
        port: int = 8091,
        config_file: str = "firewall.json",
    ):
        super().__init__(daemon=True)

        self._lock = threading.Lock()
        self.tool = tool
        self.observer = observer
        self.port = port
        self.interface = interface
        self.whitelist_hotkeys = []
        self.specifications = {}
        self.first_try = True

        self._sources = defaultdict(lambda: defaultdict(list))
        """
        List all the source of requests with their packets
        The key of a source is ip:dport:protocol, the value is a list of requests that contains packets
        """

        self._rules = []
        """
        List all the active rules       
        """

        self.monitor = FirewallMonitor(sse=sse)

        self.provider = FileLocalMonitor(
            logger_name=FIREWALL_LOGGING_NAME,
            file_path=config_file,
            check_interval=FIREWALL_SLEEP,
            callback=self.update_config,
        )

    @property
    def rules(self):
        """
        List of rules to apply
        """
        with self._lock:
            return list(self._rules)

    def start(self):
        self.monitor.start()
        super().start()
        btul.logging.debug(f"{FIREWALL_LOGGING_NAME} started")

    def stop(self):
        self.observer.stop()
        self.monitor.stop()
        super().join()
        btul.logging.debug(f"{FIREWALL_LOGGING_NAME} stopped")

    def wait(self):
        """
        Wait until we have execute the run method at least one
        """
        attempt = 1
        while self.first_try and attempt <= FIREWALL_ATTEMPTS:
            btul.logging.debug(
                f"[{FIREWALL_LOGGING_NAME}][{attempt}] Waiting file to be process..."
            )
            time.sleep(1)
            attempt += 1

    def is_whitelisted(self, hotkey: str):
        """
        True if the hotkey is whitelisted, false otherwise
        """
        is_whitelisted = False
        with self._lock:
            is_whitelisted = hotkey in self.whitelist_hotkeys

        return is_whitelisted

    def is_blacklisted(self, hotkey: str):
        """
        True if the hotkey is blacklisted, false otherwise
        """
        is_blacklisted = False
        with self._lock:
            is_blacklisted = hotkey not in self.whitelist_hotkeys

        if is_blacklisted:
            return (True, RuleType.DENY, f"Hotkey '{hotkey}' is blacklisted")

        return (False, None, None)

    def is_unknown_synapse(self, name: str):
        """
        True if the synapse is an allowed one, false otherwise
        """
        synapses = self.get_specification("synapses") or []
        if len(synapses) > 0 and name not in synapses:
            return (
                True,
                RuleType.DENY,
                f"Synapse name '{name}' not found, available {list(synapses.keys())}",
            )

        return (False, None, None)

    def is_old_neuron_version(self, version: int = 0):
        """
        True if the neuron version is greater stricly than the one required, false otherwise
        """
        version_required = int(self.get_specification("neuron_version") or 0)
        if version is None or version < version_required:
            return (
                True,
                RuleType.DENY,
                f"Neuron version {version} is outdated; version {version_required} is required.",
            )

        return (False, None, None)

    def is_signed(self, hotkey, nonce, uuid, signature, computed_body_hash):
        # Get the validator hotkey
        validator_hotkey = self.get_specification("hotkey") or ""

        # Build the keypair
        keypair = Keypair(ss58_address=hotkey)

        # Build the signature messages.
        message = f"{nonce}.{hotkey}.{validator_hotkey}.{uuid}.{computed_body_hash}"

        if not keypair.verify(message, signature):
            return (
                True,
                RuleType.DENY,
                f"Signature mismatch with {message} and {signature}",
            )

        return (False, None, None)

    def cleanup_old_packets(self, current_time, requests: dict):
        """Remove packets older than the PACKET_HISTORY_DURATION."""
        keys_to_delete = [
            key
            for key, packets in requests.items()
            if len(packets) > 0
            and current_time - packets[-1].current_time
            > FIREWALL_REQUEST_HISTORY_DURATION
        ]

        if len(keys_to_delete) == 0:
            return

        # Delete the keys in a separate loop
        for key in keys_to_delete:
            del requests[key]

    def update(self, specifications={}, whitelist_hotkeys=[]):
        """
        Update some informations coming from the miner
        """
        with self._lock:
            self.specifications = copy.deepcopy(specifications)
            self.whitelist_hotkeys = list(whitelist_hotkeys)

    def update_config(self, data):
        with self._lock:
            self._rules = [create_rule(x) for x in data]

        self.first_try = False

        btul.logging.success(
            f"[{FIREWALL_LOGGING_NAME}] File proceed successfully: {len(data)} rules loaded"
        )

    def get_specification(self, name: str):
        with self._lock:
            specifications = copy.deepcopy(self.specifications)
            return specifications.get(name)

    def get_ip_index(self, firewall_data, ip_to_find):
        for index, ip in enumerate(firewall_data.keys()):
            if ip == ip_to_find:
                return index
        return None

    def find_last_request_packet(
        self,
        packets: list[FirewallPacket],
    ) -> FirewallPacket | None:
        index = -1

        for i in range(len(packets) - 1, -1, -1):
            if packets[i].flags == "S":
                index = i
                break

        return packets[index] if index >= 0 else None

    def detect_dos(
        self,
        vps: dict,
        id,
        current_time,
        rule: DetectDoSRule,
    ):
        """
        Detect Denial of Service attack which is an attack from a single source that overwhelms a target with requests,
        """
        recent_packets = [
            request
            for request in vps[id]
            if current_time - request.current_time < rule.time_window
        ]

        if len(recent_packets) > rule.packet_threshold:
            return (
                True,
                RuleType.DETECT_DOS,
                f"DoS attack detected: {len(recent_packets)} requests in {rule.time_window} seconds",
            )

        return (False, None, None)

    def detect_ddos(self, vps, id, port, current_time, rule: DetectDDoSRule):
        """
        Detect Distributed Denial of Service which is an attack from multiple sources that overwhelms a target with requests,
        """
        # Get the index of the packet id
        index = next((i for i, x in enumerate(vps.keys()) if x == id), -1)

        # Get all the recent SYNC packet that will be used to detect any DoS attack
        recent_requests = [
            request
            for id, requests in vps.items()
            for request in requests
            if id.split(":")[1] == str(port)
            and current_time - request.current_time < rule.time_window
        ]

        # Create an array with the number of recent timestamps for each vps
        packets_count = [
            sum(
                1
                for request in requests
                if current_time - request.current_time < rule.time_window
            )
            for requests in vps.values()
        ]

        if len(recent_requests) <= rule.packet_threshold:
            return (False, None, None)

        t = np.percentile(packets_count, 75)

        legit = [x for x in packets_count if x <= t]
        max_legit = np.max(legit) if len(legit) > 0 else 0
        mean_legit = np.mean(legit) if len(legit) > 0 else 0

        ip_count = packets_count[index]

        if ip_count > max_legit + mean_legit:
            return (
                True,
                RuleType.DETECT_DDOS,
                f"DDoS attack detected: {ip_count} requests in {rule.time_window} seconds",
            )

        return (False, None, None)

    def get_rule(self, rules: List[Rule], type: RuleType, ip, port, protocol):
        filtered_rules = [r for r in rules if r.rule_type == type]

        # Ip/Port rule
        rule = next(
            (
                r
                for r in filtered_rules
                if r.ip == ip and r.dport == port and r.protocol == protocol
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
                and r.dport is None
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
                and r.dport == port
                and r.protocol == protocol
                and r.ip is None
            ),
            None,
        )

        return rule

    def get_last_deny(requests):
        pass

    def notify(
        self, current_request: FirewallRequest, packet: FirewallPacket, notified=False
    ):
        packet_event = {
            "request_id": current_request.id,
            "previous_id": current_request.previous_id if current_request else "",
            "notified": notified,
            **packet.to_dict(),
        }
        self.monitor.emit(packet_event)

    def display_date(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def check_cleaning(self, initial_sources, old_sources, new_sources):
        # if len(old_sources) + len(new_sources) != len(initial_sources):
        #     old_keys = list(old_sources.keys())
        #     new_keys = list(new_sources.keys())
        #     initial_keys = list(initial_sources.keys())

        #     btul.logging.warning(
        #         f"[CHECKING] Old sources {len(old_sources)} + New Sources {len(new_sources)} != Sources {len(initial_sources)}"
        #     )
        #     btul.logging.warning(initial_keys)
        #     btul.logging.warning(old_keys)
        #     btul.logging.warning(new_keys)
        #     return False

        for id, requests in new_sources.items():
            if len(requests) == 0:
                return

            max_time_set = max(req.max_time for req in requests)
            min_time = min(req.current_time for req in requests)
            max_time = max(req.current_time for req in requests)

            if max_time - min_time > max_time_set:
                to_remove = [
                    req for req in requests if max_time - req.current_time > 60
                ]
                max_to_remove = max(req.current_time for req in to_remove)

                if (
                    len(to_remove) == 1
                    and to_remove[0].is_denied()
                    or to_remove[0].is_allowed()
                ):
                    continue

                btul.logging.warning(
                    f"[CHECKING][{id}] {len(to_remove)} requests ({len(requests)}) exceed {max_time_set} seconds between {self.display_date(min_time)} and {self.display_date(max_time)} ({self.display_date(max_to_remove)})"
                )
                return False

        return True

    def packet_callback(self, packet: FirewallPacket):
        metadata = {}
        has_state_changed = False
        packet_already_processed = None
        current_request = None
        try:
            # Get the source ip
            if packet.sip is None:
                return

            # Get the current time
            current_time = packet.current_time

            # Get all rules related to the ip/port
            rules = [
                r for r in self.rules if r.ip == packet.sip or r.dport == packet.dport
            ]

            # Set metadata for logs purpose on exception
            metadata = {"ip": packet.sip, "dport": packet.dport}

            # Check if a allow rule exist
            match_allow_rule = (
                self.get_rule(
                    rules=rules,
                    type=RuleType.ALLOW,
                    ip=packet.sip,
                    port=packet.dport,
                    protocol=packet.protocol,
                )
                is not None
            )

            # Check if a deny rule exist
            match_deny_rule = (
                self.get_rule(
                    rules=rules,
                    type=RuleType.DENY,
                    ip=packet.sip,
                    port=packet.dport,
                    protocol=packet.protocol,
                )
                is not None
            )

            # Work with a copy of the requests
            sources = defaultdict(list)
            with self._lock:
                sources = self._sources.get(packet.queue_num, sources)

            # Initialise variables
            seq = 0

            requests = sources.get(packet.id) or []
            if len(requests) > 0:
                last_request = requests[-1]
                last_packet = last_request.get_last_packet()

                seq = last_packet.seq

            # If no rule, by default we allow packets
            must_allow = match_allow_rule
            must_deny = match_deny_rule
            is_request_for_miner = self.port == packet.dport
            rule_type = None
            reason = None

            # True if there is any explicit allow/deny rule defined
            is_decision_made = match_allow_rule or match_deny_rule

            # True is the packet is a connection initiation, false otherwise
            # packet.seq and seq will be the same if it is part of a retry
            is_sync_packet = (
                packet.seq != seq and packet.ack == 0 and packet.flags == "S"
            )

            # True if the packet is a data packet, false otherwise
            is_data_packet = packet.flags == "PA"

            # Get a packet with the same internal id than the current one
            # Due to the TCP protocol's inherent behavior of re-transmitting packets when it doesn't receive an acknowledgment from the recipient
            for request in sources.get(packet.id, []):
                packet_already_processed = request.get_packet_by_internal_id(
                    packet.internal_id
                )
                if packet_already_processed is not None:
                    break

            # If there already a packet processed with that internalid, we re-apply the same decision
            if packet_already_processed is not None:
                if packet_already_processed.status == "allow":
                    packet.accept()
                else:
                    packet.drop(
                        type=packet_already_processed.type,
                        reason=packet_already_processed.reason,
                    )

                return

            # Create the new request if SYNC packet
            if is_sync_packet:
                previous_id = (
                    sources[packet.id][-1].id
                    if len(sources) > 0 and len(sources[packet.id]) > 0
                    else None
                )
                current_request = FirewallRequest(previous_id)
                sources[packet.id].append(current_request)

            # Get the current request
            current_request = next(
                (
                    request
                    for request in reversed(sources[packet.id])
                    if is_sync_packet or request.is_part_of(packet.seq)
                ),
                None,
            )

            # Check if it is a lost packet due to restarting miner and removing firewall-events.json
            is_lost_packet = current_request is None and not is_sync_packet
            if is_lost_packet:
                packet.drop(type=RuleType.DENY, reason=f"Packet {packet.flags} lost")
                return

            # Get the previous request
            previous_request = None
            previous_id = current_request.previous_id
            while previous_request is None or previous_id is None:
                previous_request = next(
                    (x for x in sources[packet.id] if x.id == previous_id),
                    None,
                )

                if previous_request is None:
                    break

                if previous_request.is_denied():
                    break

                if is_sync_packet:
                    # It is a sync packet but it is allowed
                    break

                if len(previous_request._packets) == 2:
                    break

                previous_id = previous_request.previous_id

            # Skip any packets that are not SYNC or DATA and use the SYNC or DATA decision
            # depending on when these packets arrive
            if packet.flags not in ["S", "PA"]:
                if current_request.is_last_packet_allowed():
                    # Request is at the moment accepted, so we accept the current packet
                    packet.accept()
                else:
                    # Request is at the moment denied, so we deny the current packet with the same reason
                    latest = current_request.get_last_packet()
                    packet.drop(
                        type=latest.type,
                        reason=latest.reason,
                    )

                return

            # Add the new packet to the request (SYNC or DATA)
            current_request.add_packet(packet)

            # Get the previous packet of the current request
            current_previous_packet = current_request.get_last_packet(-2)

            # Check if it is an on-going communication or re-transmission
            # Applied the same decision as we made before
            if is_data_packet and packet.ack == current_previous_packet.ack:
                if current_previous_packet.status == "allow":
                    packet.accept()
                else:
                    packet.drop(
                        type=current_previous_packet.type,
                        reason=current_previous_packet.reason,
                    )

                return

            # Check if the SYNC packet has been deny
            sync_packet = current_request.get_sync_packet()
            if sync_packet and sync_packet.status == "deny":
                must_deny = True
                sync_packet = current_request._packets[0]
                rule_type = sync_packet.type
                reason = sync_packet.reason

            # Cheks for miner requests
            if is_request_for_miner and is_data_packet:
                # Checks only for miner, not for subtensor
                metadata = {
                    **metadata,
                    "synapse": {
                        "name": packet.headers.synapse_name,
                        "neuron_version": packet.headers.dendrite_version,
                        "hotkey": packet.headers.dendrite_hotkey,
                    },
                }

                # Check if the packet matches an expected synapses
                must_deny, rule_type, reason = (
                    self.is_unknown_synapse(packet.headers.synapse_name)
                    if not must_deny
                    else (must_deny, rule_type, reason)
                )

                # Check if the signature
                must_deny, rule_type, reason = (
                    self.is_signed(
                        packet.headers.dendrite_hotkey,
                        packet.headers.dendrite_nonce,
                        packet.headers.dendrite_uuid,
                        packet.headers.dendrite_signature,
                        packet.headers.computed_body_hash,
                    )
                    if not must_deny
                    else (must_deny, rule_type, reason)
                )

                # Check if the hotkey is blacklisted
                must_deny, rule_type, reason = (
                    self.is_blacklisted(packet.headers.dendrite_hotkey)
                    if not must_deny and not is_decision_made
                    else (must_deny, rule_type, reason)
                )

                # Check if the neuron version is greater stricly than the one required
                must_deny, rule_type, reason = (
                    self.is_old_neuron_version(packet.headers.dendrite_neuron_version)
                    if not must_deny
                    else (must_deny, rule_type, reason)
                )

                if not is_decision_made:
                    must_allow = must_allow or self.is_whitelisted(
                        packet.headers.dendrite_hotkey
                    )

            # Check if a DoS attack is found
            dos_rule = self.get_rule(
                rules=rules,
                type=RuleType.DETECT_DOS,
                ip=packet.sip,
                port=packet.dport,
                protocol=packet.protocol,
            )
            must_deny, rule_type, reason = (
                self.detect_dos(
                    sources,
                    packet.id,
                    current_time,
                    dos_rule,
                )
                if dos_rule
                and not must_deny
                and is_sync_packet
                and not is_decision_made
                else (must_deny, rule_type, reason)
            )

            # Check if a DDoS attack is found
            ddos_rule = self.get_rule(
                rules=rules,
                type=RuleType.DETECT_DDOS,
                ip=packet.sip,
                port=packet.dport,
                protocol=packet.protocol,
            )
            must_deny, rule_type, reason = (
                self.detect_ddos(
                    sources,
                    packet.id,
                    packet.dport,
                    current_time,
                    ddos_rule,
                )
                if ddos_rule
                and not must_deny
                and is_sync_packet
                and not is_decision_made
                else (must_deny, rule_type, reason)
            )

            if must_deny:
                # Drop the packet
                packet.drop(type=rule_type, reason=reason)

                # Trace the packet
                copyright = (
                    "Packet new connection"
                    if is_sync_packet
                    else "Packet data" if is_data_packet else "Packet unknown"
                )

                btul.logging.trace(
                    f"[{packet.id}][{packet.protocol}][{packet.flags}][{current_request.id}][{packet.current_time}] {copyright} dropped"
                )

                has_state_changed = previous_request is None or (
                    previous_request.is_allowed() and not current_request.notified
                )
                if has_state_changed:
                    current_request.notified = True
                    packet.notified = True
                    btul.logging.warning(
                        f"Blocking {packet.protocol} {packet.sip}/{packet.dport}: {packet.reason}"
                    )
            else:
                # Accept the packet
                packet.accept()

                # Trace the packet
                copyright = (
                    "Packet new connection"
                    if is_sync_packet
                    else "Packet data" if is_data_packet else "Packet unknown"
                )
                btul.logging.trace(
                    f"[{packet.id}][{packet.protocol}][{packet.flags}][{current_request.id}][{packet.current_time}] {copyright} allowed"
                )

                has_state_changed = (
                    not is_sync_packet
                    and previous_request
                    and previous_request.is_denied()
                    and not current_request.notified
                )
                if has_state_changed:
                    current_request.notified = True
                    packet.notified = True
                    btul.logging.success(
                        f"Unblocking {packet.protocol} {packet.sip}/{packet.dport}"
                    )

            # Set max_time for the packet
            max_time = max(
                getattr(dos_rule, "time_window", 0),
                getattr(ddos_rule, "time_window", 0),
                FIREWALL_REQUEST_HISTORY_DURATION,
            )
            packet.max_time = max_time

            # Remove old requests
            old_sources, sources2 = clean_sources(
                sources=sources,
                current_time=current_time,
            )

            # Clean the firewall file
            requests_id = [x.id for requests in old_sources.values() for x in requests]
            if len(requests_id) > 0:
                self.monitor.clean(requests_id)

            # Update the memory cache
            with self._lock:
                self._sources[packet.queue_num] = sources2

        except Exception as ex:
            btul.logging.warning(
                f"[{FIREWALL_LOGGING_NAME}] Failed to proceed firewall packet: {ex}"
            )
            btul.logging.info(f"[{FIREWALL_LOGGING_NAME}] Packet metadata: {metadata}")
            btul.logging.debug(traceback.format_exc())

        finally:
            try:
                # Set the process fime
                packet.process_time = time.time() - packet.current_time

                # Notify of the new packet if
                # - a current request exists => not a lost package
                # - packet is an identical one that has already been processed
                if current_request is not None and packet_already_processed is None:
                    self.notify(
                        packet=packet,
                        current_request=current_request,
                        notified=has_state_changed,
                    )

                # Commit the packet which mean we accept or drop it
                # Commit here to ensure we finish to process the current packet
                # before starting processing the next one
                packet.commit()
            except Exception as err:
                btul.logging.error(f"[{packet.id}] Error {err}")
                btul.logging.error(traceback.format_exc())
                raise err

    def run(self):
        # Reload the previous ips blocked
        btul.logging.debug(f"[{FIREWALL_LOGGING_NAME}] Loading events")
        packets = load_njson_file("firewall-events.json") or []

        # Group by request id
        grouped_packets = defaultdict(list)
        for packet in packets:
            grouped_packets[packet["request_id"]].append(packet)

        # Lost all the requests with their packets
        sources = defaultdict(lambda: defaultdict(list))
        for request_id, packets in grouped_packets.items():
            previous_id = packets[0].get("previous_id") if len(packets) > 0 else ""
            request = FirewallRequest.from_dict(
                {
                    "request_id": request_id,
                    "previous_id": previous_id,
                    "packets": packets,
                }
            )

            sources[request.queue_num][request.group_id].append(request)

        # Get the total of requests
        total_requests = sum(
            len(request_list)
            for group_dict in sources.values()
            for request_list in group_dict.values()
        )
        btul.logging.debug(f"[{FIREWALL_LOGGING_NAME}] Loading {total_requests} requests")

        # Update the cache
        with self._lock:
            self._sources = sources

        btul.logging.debug(f"[{FIREWALL_LOGGING_NAME}] Creating allow rule for loopback")
        self.tool.create_allow_loopback_rule()

        # Create Allow rules
        btul.logging.debug(f"[{FIREWALL_LOGGING_NAME}] Creating allow rules")
        self.tool.create_allow_rule(dport=22, protocol="tcp")
        self.tool.create_allow_rule(dport=443, protocol="tcp")
        self.tool.create_allow_rule(sport=443, protocol="tcp")
        self.tool.create_allow_rule(sport=80, protocol="tcp")
        self.tool.create_allow_rule(sport=53, protocol="udp")

        # Create queue rules
        btul.logging.debug(f"[{FIREWALL_LOGGING_NAME}] Creating queue rules")
        self.tool.create_allow_rule(dport=8091, protocol="tcp", queue=1)
        self.tool.create_allow_rule(dport=9944, protocol="tcp", queue=2)
        self.tool.create_allow_rule(dport=9933, protocol="tcp", queue=3)
        self.tool.create_allow_rule(dport=30333, protocol="tcp", queue=4)
        self.tool.create_allow_rule(sport=30333, protocol="tcp")

        # Change the policy to deny
        btul.logging.debug(
            f"[{FIREWALL_LOGGING_NAME}] Change the INPUT policy to deny by default"
        )
        self.tool.create_deny_policy()

        # Subscribe to the observer
        self.observer.subscribe(
            name="Miner", queue_num=1, callback=self.packet_callback
        )
        self.observer.subscribe(
            name="SubtensorWS", queue_num=2, callback=self.packet_callback
        )
        self.observer.subscribe(
            name="SubtensorRPC", queue_num=3, callback=self.packet_callback
        )
        self.observer.subscribe(
            name="SubtensorP2P", queue_num=4, callback=self.packet_callback
        )
        self.observer.start()
