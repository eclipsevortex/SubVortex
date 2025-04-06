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
import os

from subvortex.core.shared.file import load_json_file
from subvortex.core.file.file_provider import FileProvider


class FileLocalMonitor(FileProvider):
    """
    Class to get the up to date data from any local file
    Only json file is possible for now
    """

    def __init__(self, logger_name, file_path, check_interval, callback) -> None:
        super().__init__(logger_name, check_interval)
        self._file_path = file_path
        self._callback = callback
        self.last_modified = None

    def check_file_updated(self):
        current_time = os.path.getmtime(self._file_path)
        has_changed = current_time != self.last_modified
        self.last_modified = current_time if has_changed else self.last_modified
        return has_changed

    def load_file(self):
        data = load_json_file(self._file_path)
        return data

    def notify(self, data):
        if not self._callback:
            return

        self._callback(data)
