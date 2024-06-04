import time
import copy
import requests
import threading
import ipaddress
import bittensor as bt
from datetime import datetime
from typing import List

from subnet.country.country_constants import (
    COUNTRY_URL,
    LOGGING_NAME,
    COUNTRY_SLEEP,
)
from subnet.validator.localisation import (
    get_country_by_country_is,
    get_country_by_ip_api,
    get_country_by_ipinfo_io,
    get_country_by_my_api,
)


class CountryService(threading.Thread):
    def __init__(self, netuid: int):
        super().__init__()
        self.stop_flag = threading.Event()
        self._lock = threading.Lock()
        self._data = {}
        self.netuid = netuid
        self.last_modified = None
        self.show_not_found = True
        self.first_try = True

        # Allow us to not display multiple time the same errors
        self.error_message = None

    def _is_custom_api_enabled(self):
        with self._lock:
            return self._data.get("enable_custom_api") or True

    def get_last_modified(self):
        with self._lock:
            return self.last_modified

    def get_locations(self) -> List[str]:
        with self._lock:
            localisations = self._data.get("localisations") or {}
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

        bt.logging.warning(
            f"Could not get the country of the ip {ip_ipv4}: Api 1: {reason1} / Api 2: {reason2} / Api 3: {reason3} / Api 4: {reason4}"
        )
        return None

    def start(self):
        super().start()
        bt.logging.debug(f"Country started")

    def stop(self):
        self.stop_flag.set()
        super().join()
        bt.logging.debug(f"Country stopped")

    def wait(self):
        """
        Wait until we have execute the run method at least one
        """
        attempt = 0
        while self.first_try or attempt > 5:
            time.sleep(1)
            attempt += 1

    def run(self):
        while not self.stop_flag.is_set():
            response = None
            try:
                # Sleep before requesting again
                if not self.first_try:
                    time.sleep(COUNTRY_SLEEP)

                url = COUNTRY_URL.get(self.netuid)
                if not url:
                    bt.logging.warning(
                        f"Could not find the country file for the subnet {self.netuid}"
                    )

                response = requests.get(url)
                if response.status_code != 200:
                    if response.status_code == 404 and not self.show_not_found:
                        continue

                    self.show_not_found = response.status_code != 404

                    error_message = f"[{LOGGING_NAME}] Could not get the country file {response.status_code}: {response.reason}"
                    if error_message != self.error_message:
                        bt.logging.warning(error_message)
                        self.error_message = error_message

                    continue

                # Load the data
                data = response.json() or {}

                # Check is date can be retrieved
                remote_last_modified = data.get("last-modified")
                if remote_last_modified is None:
                    continue

                # Check if data changed
                last_modified = datetime.strptime(
                    remote_last_modified, "%Y-%m-%d %H:%M:%S.%f"
                )
                if self.last_modified and last_modified <= self.last_modified:
                    continue

                if self._data == data:
                    continue

                with self._lock:
                    self._data = data
                    self.last_modified = last_modified

                bt.logging.success(
                    f"[{LOGGING_NAME}] Country file proceed successfully",
                )
            except Exception as err:
                content = response.content if response else ""
                error_message = f"[{LOGGING_NAME}] An error during country file processing: {err} {type(err)} {content}"
                if error_message != self.error_message:
                    bt.logging.error(error_message)
                    self.error_message = error_message
            finally:
                self.first_try = False
