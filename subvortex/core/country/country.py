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
    "ipinfo": 90,  # Free tier: 1000 req/day = 86400s/1000 = 86.4s between calls - Highest accuracy (~99%)
    "ip_api": 5,  # Free tier: 45 req/min = 1.33s between calls, use 1.5s for safety (https://ip-api.com/docs/unban) - Very high accuracy (~98%)
    "country_is": 10,  # Free tier: 1 req/10 seconds per IP (https://country.is/) - Good accuracy (~95%)
    "my_api": 0,  # Custom API - Down!
}


# Per-IP per-API rate limit tracking: {ip: {api_name: last_call_time}}
_per_ip_rate_limits = {}

countries = {}


class CountryApiException(Exception):
    """Exception raised when all country APIs fail"""

    def __init__(self, message: str, rate_limited: dict = None):
        super().__init__(message)
        self.rate_limited = rate_limited or {}


def get_country(ip: str):
    """
    Get the country code of the ip with aggressive API calling until rate limited.
    Single pass through APIs - infinite retry is handled by caller.
    """
    ip_ipv4 = get_ipv4(ip)

    # APIs ordered by accuracy (highest to lowest)
    apis = [
        (_get_country_by_ipinfo_io, "ipinfo"),  # Highest accuracy (~99%)
        (_get_country_by_ip_api, "ip_api"),  # Very high accuracy (~98%)
        (_get_country_by_country_is, "country_is"),  # Good accuracy (~95%)
        # (_get_country_by_subvortex_api, "subvortex"), # Custom API - Not ready yet
        # (_get_country_by_my_api, "my_api"),         # Down
    ]

    # Initialize per-IP tracking if not exists
    if ip_ipv4 not in _per_ip_rate_limits:
        _per_ip_rate_limits[ip_ipv4] = {}

    errors = []
    rate_limited = {}
    
    for api_func, api_name in apis:
        # Check if this API is still in rate limit cooldown for this specific IP
        now = time.time()
        if api_name in _per_ip_rate_limits[ip_ipv4]:
            rate_limit_end = _per_ip_rate_limits[ip_ipv4][api_name]
            if now < rate_limit_end:
                remaining = rate_limit_end - now
                rate_limited[api_name] = remaining
                continue

        try:
            country, reason = api_func(ip_ipv4)
            if country:
                return country
            
            if reason:
                errors.append(f"{api_name}: {reason}")

        except requests.HTTPError as e:
            status_code = getattr(e.response, "status_code", "unknown")
            
            # Check for rate limit status codes
            if status_code in [429, 403]:  # Common rate limit codes
                rate_limit_duration = _extract_rate_limit_from_response(e.response, api_name)
                rate_limit_end = now + rate_limit_duration
                _per_ip_rate_limits[ip_ipv4][api_name] = rate_limit_end
                
                btul.logging.warning(
                    f"🚫 {api_name} rate limited for {ip_ipv4} (HTTP {status_code}). "
                    f"Will retry after {rate_limit_duration}s"
                )
                rate_limited[api_name] = rate_limit_duration
                
            else:
                errors.append(f"{api_name} ({status_code}): {e}")

        except Exception as e:
            # Check if error message indicates rate limiting
            error_msg = str(e).lower()
            if any(phrase in error_msg for phrase in ['rate limit', 'too many requests', 'quota exceeded']):
                # Apply default rate limit if we detect rate limiting but no HTTP status
                rate_limit_duration = API_RATE_LIMITS.get(api_name, 60)  # Default to 60s
                rate_limit_end = now + rate_limit_duration
                _per_ip_rate_limits[ip_ipv4][api_name] = rate_limit_end
                
                btul.logging.warning(
                    f"🚫 {api_name} rate limited for {ip_ipv4} (detected from error). "
                    f"Will retry after {rate_limit_duration}s"
                )
                rate_limited[api_name] = rate_limit_duration

            else:
                errors.append(f"{api_name}: {e}")

    # Combine all errors and rate limits
    all_errors = errors + [
        f"{api}: {remaining:.0f}s cooldown" for api, remaining in rate_limited.items()
    ]

    if all_errors:
        raise CountryApiException(
            f"All APIs failed for {ip_ipv4} - {'; '.join(all_errors)}", rate_limited
        )
    
    # This should not happen, but safety fallback
    raise CountryApiException(
        f"No APIs available for {ip_ipv4}", rate_limited
    )


def _extract_rate_limit_from_response(response, api_name: str) -> float:
    """
    Extract rate limit duration from HTTP response headers.
    Returns duration in seconds to wait before retrying.
    """
    try:
        # Try common rate limit headers
        headers_to_check = [
            'retry-after',           # Standard header
            'x-ratelimit-reset',     # Unix timestamp
            'x-rate-limit-reset',    # Unix timestamp  
            'x-ratelimit-retry-after', # Seconds
            'rate-limit-reset',      # Seconds
        ]
        
        for header in headers_to_check:
            if header in response.headers:
                value = response.headers[header]
                
                # Handle different formats
                if header in ['x-ratelimit-reset', 'x-rate-limit-reset']:
                    # Unix timestamp - calculate difference from now
                    try:
                        reset_time = int(value)
                        current_time = int(time.time())
                        duration = max(reset_time - current_time, 1)  # At least 1 second
                        btul.logging.debug(f"Extracted rate limit from {header}: {duration}s")
                        return float(duration)
                    except (ValueError, TypeError):
                        continue
                else:
                    # Direct seconds value
                    try:
                        duration = float(value)
                        btul.logging.debug(f"Extracted rate limit from {header}: {duration}s")
                        return max(duration, 1)  # At least 1 second
                    except (ValueError, TypeError):
                        continue
        
        # If no headers found, use the official API rate limits
        duration = API_RATE_LIMITS.get(api_name, 60)  # Default to 60s
        btul.logging.debug(f"No rate limit headers found, using default for {api_name}: {duration}s")
        return float(duration)
        
    except Exception as e:
        btul.logging.warning(f"Error extracting rate limit from response: {e}")
        return 60.0  # Safe default


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


def cleanup_rate_limits_for_ips(ips: list[str]):
    """
    Clean up rate limit tracking for specific IPs.
    Call this when neurons with these IPs are deleted from the metagraph.

    Args:
        ips: List of IP addresses to clean up
    """
    cleaned_count = 0
    for ip in ips:
        ip_ipv4 = get_ipv4(ip)
        if ip_ipv4 in _per_ip_rate_limits:
            del _per_ip_rate_limits[ip_ipv4]
            cleaned_count += 1

    if cleaned_count > 0:
        btul.logging.debug(f"🧹 Cleaned up rate limit data for {cleaned_count} IPs")

    return cleaned_count


def cleanup_rate_limits_for_api(api_name: str):
    """
    Clean up rate limit tracking for a specific API across all IPs.
    Call this if an API is permanently disabled or changed.

    Args:
        api_name: Name of the API to clean up ("ipinfo", "ip_api", "country_is", etc.)
    """
    cleaned_count = 0
    for ip_dict in _per_ip_rate_limits.values():
        if api_name in ip_dict:
            del ip_dict[api_name]
            cleaned_count += 1

    if cleaned_count > 0:
        btul.logging.debug(
            f"🧹 Cleaned up {api_name} rate limit data for {cleaned_count} IPs"
        )

    return cleaned_count


def cleanup_all_rate_limits():
    """
    Clean up all rate limit tracking data.
    Call this for complete reset or during shutdown.
    """
    global _per_ip_rate_limits
    count = len(_per_ip_rate_limits)
    _per_ip_rate_limits.clear()

    if count > 0:
        btul.logging.info(f"🧹 Cleaned up all rate limit data ({count} IPs)")

    return count
