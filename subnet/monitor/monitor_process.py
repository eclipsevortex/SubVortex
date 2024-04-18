import threading

from subnet.shared import logging as sv
from subnet.monitor.monitor_constants import LOGGING_NAME
from subnet.monitor.monitor import Monitor


class MonitorProcess(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_flag = threading.Event()
        self.monitor = Monitor()

    def run(self):
        while not self.stop_flag.is_set():
            try:
                self.monitor.run()
            except Exception as err:
                sv.logging.error(
                    f"[{LOGGING_NAME}] An error during monitoring: {err}"
                )