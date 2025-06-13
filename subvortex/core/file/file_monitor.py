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
from enum import Enum

import bittensor.utils.btlogging as btul
from subvortex.core.file.file_provider import FileProvider

LOGGER_NAME = "File Monitoring"


class FileType(Enum):
    LOCAL = "local"
    GOOGLE_DRIVE = "google-drive"


class FileMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.stop_flag = threading.Event()
        self.loop_ready = threading.Event()
        self.last_error_shown = None
        self.coroutines = []
        self.loop = None
        self._lock = threading.Lock()

    def add_file_provider(self, file_provider: FileProvider):
        # Wait indefinitely until the loop is ready
        self.loop_ready.wait()

        with self._lock:
            if self.loop and not self.loop.is_closed():
                future = asyncio.run_coroutine_threadsafe(
                    self._check_file(file_provider), self.loop
                )
                self.coroutines.append(future)
            else:
                btul.logging.error(f"[{LOGGER_NAME}] Cannot add file provider, loop closed")


    async def _check_file(self, file: FileProvider):
        try:
            while not self.stop_flag.is_set():
                await asyncio.sleep(file.check_interval)
                if self.stop_flag.is_set():
                    break

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

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop_ready.set()

        async def monitor():
            while not self.stop_flag.is_set():
                # Short sleep to yield to other tasks
                await asyncio.sleep(0.1)

        try:
            self.loop.run_until_complete(monitor())
        except Exception as err:
            btul.logging.error(f"[{LOGGER_NAME}] Loop error: {err}")
        finally:
            pending = asyncio.all_tasks(loop=self.loop)
            for task in pending:
                task.cancel()
            self.loop.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )
            self.loop.close()
            btul.logging.debug(f"[{LOGGER_NAME}] Event loop closed")

    def stop(self):
        btul.logging.info(f"[{LOGGER_NAME}] FileMonitor stopping")
        self.stop_flag.set()
        self.join()
        btul.logging.info(f"[{LOGGER_NAME}] FileMonitor stopped")
