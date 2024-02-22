import typing
from template.utils.miner import Miner

class Subtensor:
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

    # Timezone of the subtensor
    timezone: str

    # List of miner using that subtensor
    miners: typing.List[Miner] = []


