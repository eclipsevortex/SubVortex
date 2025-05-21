import bittensor.utils.btlogging as btul

from subvortex.miner.neuron.src.database import Database


async def has_duplicate_ip(database: Database, ip: str):
    # Get the list of neurons
    neurons = await database.get_neurons()

    # Compute the number of occurent for the ip
    number_occurrences = [x for x in neurons if x.ip == ip]

    return number_occurrences > 1


async def wait_until_no_multiple_occurrences(database: Database, ip: str):
    good_to_go = False

    while not good_to_go:
        # Get the list of neurons
        neurons = await database.get_neurons()

        # Compute the number of occurent for the ip
        number_occurrences = [x for x in neurons.values() if x.ip == ip]

        good_to_go = len(number_occurrences) == 1

    btul.logging.debug("Check ip occurrence successful")
