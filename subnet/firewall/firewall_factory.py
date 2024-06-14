from subnet.firewall.firewall_iptables import IptablesFirewall
from subnet.firewall.firewall_model import FirewallTool


def create_firewall_tool(name: str, *args, **kwargs) -> FirewallTool:
    if name == "iptables":
        return IptablesFirewall(*args, **kwargs)

    raise ValueError(f"Invalid firewall name: {name}")
