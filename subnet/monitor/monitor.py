import time
import requests
import threading
import bittensor as bt
from datetime import datetime
from typing import List

from subnet.monitor.monitor_constants import (
    MONITOR_URLS,
    LOGGING_NAME,
    MONITOR_SLEEP,
)


class Monitor(threading.Thread):
    def __init__(self, netuid: int):
        super().__init__()
        self.stop_flag = threading.Event()
        self._lock = threading.Lock()
        self._data = {}

        self.netuid = netuid
        self.last_modified = None
        self.show_not_found = True
        self.hash = None

        # Allow us to not display multiple time the same errors
        self.error_message = None

    def get_suspicious_uids(self) -> List[int]:
        with self._lock:
            suspicious = self._data.get("suspicious") or []
            return list(suspicious)

    def start(self):
        super().start()
        bt.logging.debug(f"Monitoring started")

    def stop(self):
        self.stop_flag.set()
        super().join()
        bt.logging.debug(f"Monitoring stopped")

    def run(self):
        while not self.stop_flag.is_set():
            response = None
            try:
                # Sleep before requesting again
                time.sleep(MONITOR_SLEEP)

                url = MONITOR_URLS.get(self.netuid)
                if not url:
                    bt.logging.warning(
                        f"Could not find the monitoring file for the subnet {self.netuid}"
                    )

                response = requests.get(url)
                if response.status_code != 200:
                    if response.status_code == 404 and not self.show_not_found:
                        continue

                    self.show_not_found = response.status_code != 404

                    error_message = f"[{LOGGING_NAME}] Could not get the monitored file {response.status_code}: {response.reason}"
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

                self.last_modified = last_modified

                # Update the list
                with self._lock:
                    self._data = data

                bt.logging.success(
                    f"[{LOGGING_NAME}] Monitored file proceed successfully",
                )
                self.error_message = None
            except Exception as err:
                content = response.content if response else ""
                error_message = f"[{LOGGING_NAME}] An error during monitoring: {err} {type(err)} {content}"
                if error_message != self.error_message:
                    bt.logging.error(error_message)
                    self.error_message = error_message