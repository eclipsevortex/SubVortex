import ipaddress


def is_valid_ipv4(ip: str):
    if not isinstance(ip, str):
        return False

    try:
        return isinstance(ipaddress.ip_address(ip), ipaddress.IPv4Address)
    except ValueError:
        return False
