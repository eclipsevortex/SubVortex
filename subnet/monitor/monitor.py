import time
import threading
import bittensor as bt
from typing import List

from subnet.file.file_google_drive_monitor import FileGoogleDriveMonitor
from subnet.monitor.monitor_constants import (
    MONITOR_URLS,
    MONITOR_LOGGING_NAME,
    MONITOR_SLEEP,
    MONITOR_ATTEMPTS,
)


class Monitor:
    def __init__(self, netuid: int):
        super().__init__()
        self.stop_flag = threading.Event()
        self._lock = threading.Lock()
        self._data = {}
        self.first_try = True

        self.provider = FileGoogleDriveMonitor(
            logger_name=MONITOR_LOGGING_NAME,
            file_url=MONITOR_URLS.get(netuid),
            check_interval=MONITOR_SLEEP,
            callback=self.run,
        )

    def get_suspicious_uids(self) -> List[int]:
        with self._lock:
            suspicious = self._data.get("suspicious") or []
            return list(suspicious)

    def wait(self):
        """
        Wait until we have execute the run method at least one
        """
        attempt = 1
        while self.first_try and attempt <= MONITOR_ATTEMPTS:
            bt.logging.debug(f"[{MONITOR_LOGGING_NAME}][{attempt}] Waiting file to be process...")
            time.sleep(1)
            attempt += 1

    def run(self, data):
        with self._lock:
            self._data = data

        self.first_try = False

        bt.logging.success(
            f"[{MONITOR_LOGGING_NAME}] File proceed successfully",
        )
