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
import copy
import time
import threading
import ipaddress
import bittensor.utils.btlogging as btul
from typing import List

from subvortex.core.country.country_constants import (
    COUNTRY_URL,
    COUNTRY_LOGGING_NAME,
    COUNTRY_SLEEP,
    COUNTRY_ATTEMPTS
)
from subvortex.core.file.file_google_drive_monitor import FileGoogleDriveMonitor
from subvortex.core.localisation import (
    get_country_by_country_is,
    get_country_by_ip_api,
    get_country_by_ipinfo_io,
    get_country_by_my_api,
)


class CountryService:
    def __init__(self, netuid: int):
        self._lock = threading.Lock()
        self._data = {}
        self.first_try = True

        self.provider = FileGoogleDriveMonitor(
            logger_name=COUNTRY_LOGGING_NAME,
            file_url=COUNTRY_URL.get(netuid),
            check_interval=COUNTRY_SLEEP,
            callback=self.run,
        )

    def _is_custom_api_enabled(self):
        with self._lock:
            return self._data.get("enable_custom_api", True)

    def get_last_modified(self):
        with self._lock:
            return self._data.get("last-modified")

    def get_locations(self) -> List[str]:
        with self._lock:
            localisations = self._data.get("localisations", {})
            return copy.deepcopy(localisations)

    def get_ipv4(self, ip):
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

    def get_country(self, ip: str):
        """
        Get the country code of the ip
        """
        ip_ipv4 = self.get_ipv4(ip)

        country = None
        with self._lock:
            overrides = self._data.get("overrides") or {}
            country = overrides.get(ip_ipv4)

        if country:
            return country

        country, reason1 = (
            get_country_by_my_api(ip_ipv4)
            if self._is_custom_api_enabled()
            else (None, None)
        )
        if country:
            return country

        country, reason2 = get_country_by_country_is(ip_ipv4)
        if country:
            return country

        country, reason3 = get_country_by_ip_api(ip_ipv4)
        if country:
            return country

        country, reason4 = get_country_by_ipinfo_io(ip_ipv4)
        if country:
            return country

        btul.logging.warning(
            f"Could not get the country of the ip {ip_ipv4}: Api 1: {reason1} / Api 2: {reason2} / Api 3: {reason3} / Api 4: {reason4}"
        )
        return None

    def wait(self):
        """
        Wait until we have execute the run method at least one
        """
        attempt = 1
        while self.first_try and attempt <= COUNTRY_ATTEMPTS:
            btul.logging.debug(f"[{COUNTRY_LOGGING_NAME}][{attempt}] Waiting file to be process...")
            time.sleep(1)
            attempt += 1

    def run(self, data):
        with self._lock:
            self._data = data

        self.first_try = False

        btul.logging.success(
            f"[{COUNTRY_LOGGING_NAME}] File proceed successfully",
        )
