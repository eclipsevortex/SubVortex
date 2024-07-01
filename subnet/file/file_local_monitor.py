import os
import bittensor as bt

from subnet.shared.file import load_json_file
from subnet.file.file_provider import FileProvider


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
