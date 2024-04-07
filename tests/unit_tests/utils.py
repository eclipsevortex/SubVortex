import random
import ipaddress


def generate_random_ip():
    return str(ipaddress.IPv4Address(random.randint(0, 2**32 - 1)))
