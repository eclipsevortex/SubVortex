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
import os
import subprocess

from subnet.firewall.firewall_tool import FirewallTool


class FirewallLinuxTool(FirewallTool):
    def __init__(self):
        self.user_pf_rules_file = os.path.expanduser("~/pf_rules.conf")
        self._ensure_rules_file_exists()

    def rule_exists(
        self, ip=None, sport=None, dport=None, protocol="tcp", allow=True, queue=None
    ):
        rule = self._build_rule(ip, sport, dport, protocol, allow, queue)
        with open(self.user_pf_rules_file, "r") as f:
            return rule in f.read()

    def flush_input_chain(self):
        with open(self.user_pf_rules_file, "w") as f:
            f.write("")
        self._reload_pf()
        return True

    def create_deny_policy(self):
        rule = "block drop all"
        if self.rule_exists(
            ip=None, sport=None, dport=None, protocol="tcp", allow=False, queue=None
        ):
            return False
        self._write_rule(rule)
        return True

    def create_allow_policy(self):
        rule = "pass all"
        if self.rule_exists(
            ip=None, sport=None, dport=None, protocol="tcp", allow=True, queue=None
        ):
            return False
        self._write_rule(rule)
        return True

    def create_allow_loopback_rule(self):
        rule = "pass quick on lo0 all"
        if self.rule_exists(
            ip=None, sport=None, dport=None, protocol="tcp", allow=True, queue=None
        ):
            return False
        self._write_rule(rule)
        return True

    def create_allow_rule(
        self, ip=None, sport=None, dport=None, protocol="tcp", queue=None
    ):
        """
        Create an allow rule in the pf rules
        """
        if self.rule_exists(
            ip=ip, sport=sport, dport=dport, protocol=protocol, allow=True, queue=queue
        ):
            return False
        rule = self._build_rule(ip, sport, dport, protocol, True, queue)
        self._write_rule(rule)
        return True

    def create_deny_rule(self, ip=None, sport=None, dport=None, protocol="tcp"):
        """
        Create a deny rule in the pf rules
        """
        if self.rule_exists(
            ip=ip, sport=sport, dport=dport, protocol=protocol, allow=False, queue=None
        ):
            return False
        rule = self._build_rule(ip, sport, dport, protocol, False)
        self._write_rule(rule)
        return True

    def remove_rule(
        self, ip=None, sport=None, dport=None, protocol="tcp", allow=True, queue=None
    ):
        """
        Remove a rule in the pf rules
        """
        if not self.rule_exists(
            ip=ip, sport=sport, dport=dport, protocol=protocol, allow=allow, queue=queue
        ):
            return False
        rule = self._build_rule(ip, sport, dport, protocol, allow, queue)
        self._remove_rule_from_file(rule)
        self._reload_pf()
        return True

    def _build_rule(self, ip, sport, dport, protocol, allow, queue=None):
        action = "pass in" if allow else "block drop in"
        rule = f"{action} proto {protocol}"
        if ip:
            rule += f" from {ip}"
        if sport:
            rule += f" from any port {sport}"
        if dport:
            rule += f" to any port {dport}"
        if queue:
            rule += f" queue {queue}"
        return rule

    def _remove_rule_from_file(self, rule):
        with open(self.user_pf_rules_file, "r") as f:
            rules = f.readlines()
        with open(self.user_pf_rules_file, "w") as f:
            for r in rules:
                if r.strip() != rule.strip():
                    f.write(r)

    def _ensure_rules_file_exists(self):
        if not os.path.isfile(self.user_pf_rules_file):
            with open(self.user_pf_rules_file, "w") as f:
                f.write("")

    def _reload_pf(self):
        subprocess.run(["sudo", "/sbin/pfctl", "-f", "/etc/pf.conf"], check=True)
        if not self._is_pf_enabled():
            subprocess.run(["sudo", "pfctl", "-e"], check=True)

    def _is_pf_enabled(self):
        result = subprocess.run(
            ["sudo", "pfctl", "-s", "info"], capture_output=True, text=True
        )
        return "Status: Enabled" in result.stdout

    def _write_rule(self, rule):
        with open(self.user_pf_rules_file, "a") as f:
            f.write(f"{rule}\n")
        self._reload_pf()
