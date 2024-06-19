import subprocess

from subnet.firewall.firewall_model import FirewallTool


class IptablesFirewall(FirewallTool):
    def rule_exists(self, ip=None, sport=None, dport=None, protocol="tcp", allow=True):
        commands = ["sudo", "iptables", "-C", "INPUT"]

        if ip is not None:
            commands += ["-s", ip]

        if dport is not None:
            commands += ["-p", protocol, "--dport", str(dport)]
        elif sport is not None:
            commands += ["-p", protocol, "--sport", str(sport)]

        if ip or sport or dport:
            commands += ["-j", "ACCEPT" if allow else "DROP"]
        else:
            commands += ["ACCEPT" if allow else "DROP"]

        result = subprocess.run(
            commands, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return result.returncode == 0

    def create_deny_policy(self):
        commands = ["sudo", "iptables", "-P", "INPUT", "DROP"]

        subprocess.run(
            commands,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return True

    def create_allow_loopback_rule(self):
        commands = ["sudo", "iptables", "-C", "INPUT", "-i", "lo", "-j", "ACCEPT"]
        result = subprocess.run(
            commands, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        if result.returncode == 0:
            return

        commands = ["sudo", "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"]

        subprocess.run(
            commands,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return True

    def create_allow_rule(self, ip=None, sport=None, dport=None, protocol="tcp"):
        """
        Create an allow rule in the iptables
        """
        if self.rule_exists(
            ip=ip, sport=sport, dport=dport, protocol=protocol, allow=True
        ):
            return False

        commands = ["sudo", "iptables", "-A", "INPUT"]
        if ip is not None:
            commands += ["-s", ip]

        if dport is not None:
            commands += ["-p", protocol, "--dport", str(dport)]
        elif sport is not None:
            commands += ["-p", protocol, "--sport", str(sport)]

        if ip or sport or dport:
            commands += ["-j", "ACCEPT"]
        else:
            commands += ["ACCEPT"]

        subprocess.run(
            commands,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return True

    def create_deny_rule(self, ip=None, sport=None, dport=None, protocol="tcp"):
        """
        Create a deny rule in the iptables
        """
        if self.rule_exists(
            ip=ip, sport=sport, dport=dport, protocol=protocol, allow=False
        ):
            return False

        commands = ["sudo", "iptables", "-I", "INPUT"]
        if ip is not None:
            commands += ["-s", ip]

        if dport is not None:
            commands += ["-p", protocol, "--dport", str(dport)]
        elif sport is not None:
            commands += ["-p", protocol, "--sport", str(sport)]

        if ip or sport or dport:
            commands += ["-j", "DROP"]
        else:
            commands += ["DROP"]

        subprocess.run(
            commands,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return True

    def remove_rule(self, ip=None, sport=None, dport=None, protocol="tcp", allow=True):
        """
        Remove a rule in the iptables
        """
        if not self.rule_exists(
            ip=ip, sport=sport, dport=dport, protocol=protocol, allow=False
        ):
            return False

        commands = ["sudo", "iptables", "-D", "INPUT"]
        if ip is not None:
            commands += ["-s", ip]

        if dport is not None:
            commands += ["-p", protocol, "--dport", str(dport)]
        elif sport is not None:
            commands += ["-p", protocol, "--sport", str(sport)]

        commands += ["-j", "ACCEPT" if allow else "DROP"]

        subprocess.run(
            commands,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return True
