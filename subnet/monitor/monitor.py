import json
import requests
import threading
from typing import List

from subnet.shared import logging as sv
from subnet.monitor.monitor_constants import MONITOR_URL, LOGGING_NAME, LOGGING_DELTA

{"suspicious": [28]}


class Monitor:
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._data = {}

        self.last_modified = None

    def get_suspicious_uids(self) -> List[int]:
        with self._lock:
            suspicious = self._data.get("suspicious") or []
            return list(suspicious)

    def run(self):
        response = requests.get(MONITOR_URL)
        if response.status_code != 200:
            sv.logging.warn(
                f"[{LOGGING_NAME}] Could not get the monitored file {response.status_code}: {response.reason}",
                silence_period=LOGGING_DELTA,
            )
            return

        last_modified = response.headers.get("Last-Modified")
        if self.last_modified == last_modified:
            return

        sv.logging.info(
            f"[{LOGGING_NAME}] Monitored file has changed",
            silence_period=LOGGING_DELTA,
        )

        # Store tag for future comparaison
        self.last_modified = last_modified

        # Load the data
        data = response.json()

        # Update the list
        with self._lock:
            self._data = data

        sv.logging.success(
            f"[{LOGGING_NAME}] Monitored file proceed successfully",
            silence_period=LOGGING_DELTA,
        )
