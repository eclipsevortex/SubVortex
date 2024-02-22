import torch

class Miner:
    # Id of the miner
    uid: torch.Tensor

    # Ip of the miner
    ip: str

    # True if the miner is hosted on the same server as the subtensor
    with_subtensor: bool


