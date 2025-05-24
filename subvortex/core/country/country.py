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
import requests
import ipaddress

MY_API_BASE_URL = "http://api.ip-from.com"
COUNTRY_IS_BASE_URL = "https://api.country.is"
IP_API_BASE_URL = "http://ip-api.com/json"
IPINFO_IO_BASE_URL = "https://ipinfo.io"

countries = {}


def get_country(ip: str):
    """
    Get the country code of the ip
    """
    ip_ipv4 = get_ipv4(ip)

    country, reason1 = _get_country_by_my_api(ip_ipv4)
    if country:
        return country

    country, reason2 = _get_country_by_country_is(ip_ipv4)
    if country:
        return country

    country, reason3 = _get_country_by_ip_api(ip_ipv4)
    if country:
        return country

    country, reason4 = _get_country_by_ipinfo_io(ip_ipv4)
    if country:
        return country

    return None


def _get_country_by_my_api(ip: str):
    """
    Get the country code of the ip (use Maxwind and IpInfo)
    Reference: http://api.ip-from.com
    """
    url = f"{MY_API_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    # New property to use
    country = data.get("country")

    # Depcreated
    country = country or data.get("maxmind_country")
    country = country or data.get("ipinfo_country")

    return (country, None)


def _get_country_by_country_is(ip: str):
    """
    Get the country code of the ip
    Reference: https://country.is/
    """
    url = f"{COUNTRY_IS_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    return data.get("country"), None


def _get_country_by_ip_api(ip: str):
    """
    Get the country code of the ip
    Reference: https://ip-api.com/
    """
    url = f"{IP_API_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    return data.get("countryCode"), None


def _get_country_by_ipinfo_io(ip: str):
    """
    Get the country code of the ip
    Reference: https://ipinfo.io/
    """
    url = f"{IPINFO_IO_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    return data.get("country"), None


def get_ipv4(ip):
    try:
        # First, try to interpret the input as an IPv4 address
        ipv4 = ipaddress.IPv4Address(ip)
        return str(ipv4)
    except ipaddress.AddressValueError:
        pass

    try:
        # Next, try to interpret the input as an IPv6 address
        ipv6 = ipaddress.IPv6Address(ip)
        if ipv6.ipv4_mapped:
            return str(ipv6.ipv4_mapped)
    except ipaddress.AddressValueError:
        pass

    return ip
