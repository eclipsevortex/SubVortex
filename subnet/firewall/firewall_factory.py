from subnet.firewall.firewall_iptables import IptablesFirewall
from subnet.firewall.firewall_observer import FirewallObserver
from subnet.firewall.firewall_linux_observer import FirewallLinuxObserver
from subnet.firewall.firewall_tool import FirewallTool
from subnet.shared.platform import is_linux_platform, get_os


def create_firewall_tool(*args, **kwargs) -> FirewallTool:
    if is_linux_platform():
        return IptablesFirewall(*args, **kwargs)

    raise ValueError(f"No firewall tool implemented for {get_os()}")


def create_firewall_observer(*args, **kwargs) -> FirewallObserver:
    if is_linux_platform():
        return FirewallLinuxObserver(*args, **kwargs)

    raise ValueError(f"No firewall observer implemented for {get_os()}")
