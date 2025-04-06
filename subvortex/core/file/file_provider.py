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
from abc import ABC, abstractmethod


class FileProvider(ABC):
    def __init__(self, logger_name: str, check_interval: int) -> None:
        self._logger_name = logger_name
        self._check_interval = check_interval
        self.skip_check_interval = True

    @property
    def logger_name(self):
        return self._logger_name

    @property
    def check_interval(self):
        if self.skip_check_interval:
            return 0

        return self._check_interval

    @abstractmethod
    def check_file_updated(self):
        pass

    @abstractmethod
    def load_file(self):
        pass

    @abstractmethod
    def notify(self, data):
        pass
