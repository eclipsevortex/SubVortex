from typing import List
import bittensor.utils.btlogging as btul

from subvortex.core.model.neuron import Neuron
from subvortex.miner.neuron.src.database import Database


async def wait_until_no_multiple_occurrences(database: Database, ip: str):
    good_to_go = False

    while not good_to_go:
        # Get the list of neurons
        neurons = await database.get_neurons()

        # Compute the number of occurent for the ip
        number_occurrences = [x for x in neurons.values() if x.ip == ip]

        good_to_go = len(number_occurrences) == 1

    btul.logging.debug("Check ip occurrence successful")


def get_validators(neurons: List[Neuron], weights_min_stake: int = 0):
    return [x for x in neurons if x.stake >= weights_min_stake]
