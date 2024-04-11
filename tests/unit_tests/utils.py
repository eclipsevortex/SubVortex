import random
import ipaddress
from collections import Counter


def generate_random_ip():
    return str(ipaddress.IPv4Address(random.randint(0, 2**32 - 1)))


def count_unique(arr):
    return len(list(set(arr)))


def count_non_unique(arr):
    return sum(1 for count in Counter(arr).values() if count > 1)
