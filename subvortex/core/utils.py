import ipaddress


def is_valid_ipv4(ip: str):
    if not isinstance(ip, str):
        return False

    try:
        # Try to interpret the input as an IPv4 address
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        pass

    try:
        # If it's an IPv6 address, check if it's IPv4-mapped
        ipv6 = ipaddress.IPv6Address(ip)
        return ipv6.ipv4_mapped is not None
    except ipaddress.AddressValueError:
        pass

    return False
