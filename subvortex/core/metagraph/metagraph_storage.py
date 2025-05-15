import typing
from abc import ABC, abstractmethod

import subvortex.core.metagraph.models as scmm


class MetagraphStorage(ABC):
    @abstractmethod
    async def set_neurons(self, neurons: typing.List[scmm.Neuron]):
        pass

    @abstractmethod
    async def get_neuron(self, hotkey: str) -> typing.List[scmm.Neuron]:
        pass

    @abstractmethod
    async def get_neurons(self) -> typing.List[scmm.Neuron]:
        pass

    @abstractmethod
    async def delete_neurons(self, hotkeys: list[str]):
        pass

    @abstractmethod
    async def mark_as_ready(self):
        pass

    @abstractmethod
    async def mark_as_unready(self):
        pass

    @abstractmethod
    async def notify_state(self):
        pass
