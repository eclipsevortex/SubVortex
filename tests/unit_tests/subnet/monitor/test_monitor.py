import time
import requests
import csv
import threading
import math
import bittensor as bt
from datetime import datetime
from typing import List
from io import StringIO

LOGGING_NAME = "Monitor"
MONITOR_URL = (
    "http://drive.google.com/uc?id=19-wcIOI3xwmJfD7sUJWy-f6UVfJCztyGL&export=download"
)
LOGGING_DELTA = 1 * 60  # Every 15 minutes


class MisbehaviorMonitor(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_flag = threading.Event()
        self._lock = threading.Lock()
        self._list = []

        self.last_modified = None
        self.previous_log_time = 0

    def get_misbehavior_uids(self) -> List[int]:
        with self._lock:
            return list(self._list)

    def log(self, message, level="info"):
        # Get current time
        current_time = time.time()

        # Compute the different between the two timestamp
        delta = math.floor(current_time - self.previous_log_time)
        if delta <= LOGGING_DELTA:
            return

        logger = getattr(bt.logging, level)
        if not logger:
            return

        logger(message)
        self.previous_log_time = current_time

    def run(self):
        while not self.stop_flag.is_set():
            try:
                time.sleep(1)

                response = requests.get(MONITOR_URL)
                if response.status_code != 200:
                    self.log(
                        f"[{LOGGING_NAME}] Could not get the monitored file {response.status_code}: {response.reason}",
                        "warning",
                    )
                    continue

                last_modified = response.headers.get("Last-Modified")
                if self.last_modified == last_modified:
                    continue

                # Store tag for future comparaison
                self.last_modified = last_modified

                # Create a CSV reader object
                reader = csv.reader(StringIO(response.text))

                # Read and process each row
                miners = []
                for row in reader:
                    miners.append(int(row[0]))

                # Update the list
                with self._lock:
                    self._list = list(miners)

                self.log(
                    f"[{LOGGING_NAME}] Monitored file proceed successfully", "success"
                )
            except Exception as err:
                bt.logging.error(
                    f"[{LOGGING_NAME}] Failed to get the monitored file: {err}"
                )
                pass

    def stop(self):
        self.stop_flag.set()