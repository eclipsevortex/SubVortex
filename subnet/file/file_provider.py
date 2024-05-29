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
