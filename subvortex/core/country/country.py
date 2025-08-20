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
import time

import bittensor.utils.btlogging as btul

SV_API_BASE_URL = "http://geo.subvortex.info"
MY_API_BASE_URL = "http://api.ip-from.com"
COUNTRY_IS_BASE_URL = "https://api.country.is"
IP_API_BASE_URL = "http://ip-api.com/json"
IPINFO_IO_BASE_URL = "https://ipinfo.io"

# Per-API rate limits (seconds between calls)
API_RATE_LIMITS = {
    "subvortex": 60,  # SubVortex API - conservative
    "ipinfo": 86.4,  # Free tier: 1000 req/day = 86400s/1000 = 86.4s between calls - Highest accuracy (~99%)
    "ip_api": 1.5,  # Free tier: 45 req/min = 1.33s between calls, use 1.5s for safety (https://ip-api.com/docs/unban) - Very high accuracy (~98%)
    "country_is": 10,  # Free tier: 1 req/10 seconds per IP (https://country.is/) - Good accuracy (~95%)
    "my_api": 0,  # Custom API - Down!
}


# Simple tracking
_last_call_time = {}

countries = {}


class CountryApiException(Exception):
    """Exception raised when all country APIs fail"""

    def __init__(self, message: str, rate_limited: dict = None):
        super().__init__(message)
        self.rate_limited = rate_limited or {}


def get_country(ip: str):
    """
    Get the country code of the ip
    """
    ip_ipv4 = get_ipv4(ip)
    errors = []
    rate_limited = {}

    # APIs ordered by accuracy (highest to lowest)
    apis = [
        (_get_country_by_ipinfo_io, "ipinfo"),        # Highest accuracy (~99%)
        (_get_country_by_ip_api, "ip_api"),           # Very high accuracy (~98%)  
        (_get_country_by_country_is, "country_is"),   # Good accuracy (~95%)
        (_get_country_by_subvortex_api, "subvortex"), # Custom API
        # (_get_country_by_my_api, "my_api"),         # Down
    ]

    for api_func, api_name in apis:
        # Check if this API is still in cooldown
        now = time.time()
        last_call = _last_call_time.get(api_name, 0)
        cooldown = API_RATE_LIMITS[api_name]

        if now - last_call < cooldown:
            remaining = cooldown - (now - last_call)
            rate_limited[api_name] = remaining
            continue

        try:
            _last_call_time[api_name] = now
            country, reason = api_func(ip_ipv4)
            if country:
                return country
            if reason:
                errors.append(f"{api_name}: {reason}")

        except Exception as e:
            errors.append(f"{api_name}: {e}")

    # Build error message with rate limit info
    all_errors = errors + [
        f"{api}: {remaining:.0f}s cooldown" for api, remaining in rate_limited.items()
    ]
    raise CountryApiException(
        f"All APIs failed for {ip_ipv4}: {'; '.join(all_errors)}", rate_limited
    )


def _get_country_by_subvortex_api(ip: str):
    """
    Get the country code of the ip (use Maxwind and IpInfo)
    Reference: http://geo.subvortex.info
    """
    url = f"{SV_API_BASE_URL}/country/{ip}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    country = data.get("country")

    return (country, None) if country else (None, "No country in response")


def _get_country_by_my_api(ip: str):
    """
    Get the country code of the ip (use Maxwind and IpInfo)
    Reference: http://api.ip-from.com
    """
    url = f"{MY_API_BASE_URL}/{ip}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    country = (
        data.get("country") or data.get("maxmind_country") or data.get("ipinfo_country")
    )

    return (country, None) if country else (None, "No country in response")


def _get_country_by_country_is(ip: str):
    """
    Get the country code of the ip
    Reference: https://country.is/
    """
    url = f"{COUNTRY_IS_BASE_URL}/{ip}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    country = data.get("country")

    return (country, None) if country else (None, "No country in response")


def _get_country_by_ip_api(ip: str):
    """
    Get the country code of the ip
    Reference: https://ip-api.com/
    """
    url = f"{IP_API_BASE_URL}/{ip}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    country = data.get("countryCode")

    return (country, None) if country else (None, "No country in response")


def _get_country_by_ipinfo_io(ip: str):
    """
    Get the country code of the ip
    Reference: https://ipinfo.io/
    """
    url = f"{IPINFO_IO_BASE_URL}/{ip}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    country = data.get("country")

    return (country, None) if country else (None, "No country in response")


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
