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
import requests
import bittensor.utils.btlogging as btul
from datetime import datetime

from subvortex.core.file.file_provider import FileProvider


class FileGoogleDriveMonitor(FileProvider):
    """
    Class to get the up to date data from any direct download link
    """

    def __init__(self, logger_name, file_url, check_interval, callback) -> None:
        super().__init__(logger_name, check_interval)
        self._file_url = file_url
        self._cache = None
        self._callback = callback
        self.last_error_shown = None
        self.last_modified = None

    def check_file_updated(self):
        # Have to return true, as we need to download the data to check if the data has changed
        return True

    def load_file(self):
        response = requests.get(self._file_url)
        if response.status_code == 200:
            self.last_error_shown = None
            return response.json()

        content = response.content if response else ""

        error_message = f"[{self.logger_name}] Failed loading data {response.status_code}: {response.reason} {content}"
        if error_message != self.last_error_shown:
            btul.logging.warning(error_message)
            self.last_error_shown = error_message

    def notify(self, data):
        if not self._has_changed(data):
            btul.logging.debug(f"[{self.logger_name}] File has not changed")
            return

        # Save the updated data
        self._cache = data

        if not self._callback:
            return

        self._callback(data)

    def _has_changed(self, data):
        """
        True if the data has changed, False otherwise
        """

        # Check is date can be retrieved
        remote_last_modified = data.get("last-modified")
        if remote_last_modified is None:
            return False

        # Check if data changed
        last_modified = datetime.strptime(remote_last_modified, "%Y-%m-%d %H:%M:%S.%f")
        if self.last_modified and last_modified <= self.last_modified:
            return False

        # Store the new last modified
        self.last_modified = last_modified

        # Check if data are the same
        if self._cache == data:
            return False

        return True
