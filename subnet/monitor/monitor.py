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
import time
import threading
import bittensor.utils.btlogging as btul
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
            btul.logging.debug(f"[{MONITOR_LOGGING_NAME}][{attempt}] Waiting file to be process...")
            time.sleep(1)
            attempt += 1

    def run(self, data):
        with self._lock:
            self._data = data

        self.first_try = False

        btul.logging.success(
            f"[{MONITOR_LOGGING_NAME}] File proceed successfully",
        )
