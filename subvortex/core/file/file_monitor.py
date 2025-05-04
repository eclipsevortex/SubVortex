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
import asyncio
import threading
import bittensor.utils.btlogging as btul
from enum import Enum

from subvortex.core.file.file_provider import FileProvider


LOGGER_NAME = "File Monitoring"


class FileType(Enum):
    LOCAL = "local"
    GOOGLE_DRIVE = "google-drive"


class FileMonitor(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_flag = threading.Event()
        self.last_error_shown = None
        self.coroutines = []
        self.loop = asyncio.new_event_loop()

    def add_file_provider(self, file_provider: FileProvider):
        task = self.loop.create_task(self._check_file(file_provider))
        self.coroutines.append(task)

    async def _check_file(self, file: FileProvider):
        while not self.stop_flag.is_set():
            try:
                # Wait a specific time before starting
                await asyncio.sleep(file.check_interval)

                btul.logging.debug(
                    f"[{LOGGER_NAME}][{file.logger_name}] Checking file..."
                )

                # Do not skip the sleep anymore
                file.skip_check_interval = False

                # Check file has been updated
                if not file.check_file_updated():
                    btul.logging.debug(
                        f"[{LOGGER_NAME}][{file.logger_name}] File has not changed"
                    )
                    continue

                # Load the file
                data = file.load_file()

                # Notify observers
                file.notify(data)

                # Reset the last error shown
                self.last_error_shown = None
            except Exception as err:
                error_message = f"[{LOGGER_NAME}][{file.logger_name}] Failed processing file: {err} {type(err)}"
                if error_message != self.last_error_shown:
                    btul.logging.error(error_message)
                    self.last_error_shown = error_message

    async def _run_async(self):
        while not self.stop_flag.is_set():
            try:
                # Sleep for a second before gathering tasks
                await asyncio.sleep(1)

                if self.stop_flag.is_set():
                    # Time to stop the file monitoring
                    # We wait until all the tasks are finished
                    await asyncio.gather(*self.coroutines)
            except Exception as err:
                error_message = (
                    f"[{LOGGER_NAME}] Failed checking files: {err} {type(err)}"
                )
                if error_message != self.last_error_shown:
                    btul.logging.error(error_message)
                    self.last_error_shown = error_message

    def run(self):
        try:
            self.loop.run_until_complete(self._run_async())
        finally:
            self.loop.stop()
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

        btul.logging.debug(f"[{LOGGER_NAME}] run ended")

    def start(self):
        super().start()
        btul.logging.debug(f"[{LOGGER_NAME}] started")

    def stop(self):
        self.stop_flag.set()
        super().join()
        btul.logging.debug(f"[{LOGGER_NAME}] stopped")
