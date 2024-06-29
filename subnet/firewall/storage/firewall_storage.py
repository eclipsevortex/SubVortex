from abc import ABC, abstractmethod

class FileStorage(ABC):
    @abstractmethod
    def get_all():
        pass

    @abstractmethod
    def get(key: str):
        pass

    @abstractmethod
    def add(key: str, value: str):
        pass

    @abstractmethod
    def remove(key: str, value: str):
        pass
