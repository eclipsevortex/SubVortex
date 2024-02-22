import torch
import typing
from template.utils.miner import Miner

class Subtensor:
    def __init__(self):
        self.miners = []

    # Ip of the subtensor
    ip: str

    # Cold key associated to the subtensor
    cold_key: str

    # Country of the subtensor
    country: str

    # Region of the subtensor
    region: str

    # City of the subtensor
    city: str

    @property
    def timezone(self):
        return f"{self.country} {self.region} {self.city}"

    # List of miner using that subtensor
    miners: typing.List[Miner]

    # Network Bandwidth
    download: float
    upload: float

    # Latency in milliseconds
    latency: float


class Miner:
    # Id of the miner
    uid: torch.Tensor

    # Ip of the miner
    ip: str

    # True if the miner is hosted on the same server as the subtensor
    with_subtensor: bool


