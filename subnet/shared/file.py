import os
import json
import bittensor as bt

from subnet.shared.encoder import EnumEncoder


def save_json_file(file: str, items):
    """
    Save the items in a json file
    """
    try:
        with open(file, "w") as file:
            data = json.dumps(items, indent=4, cls=EnumEncoder)
            file.write(data)
    except Exception as err:
        bt.logging.warning(f"Could not save the data in {file}: {err}")


def load_njson_file(file: str):
    """
    Load the njson file
    """
    data = []

    if not os.path.exists(file):
        return data

    try:
        with open(file, "r") as file:
            for line in file:
                data.append(json.loads(line))
    except Exception as err:
        bt.logging.warning(f"Could not load the data from {file}: {err}")

    return data


def load_json_file(file: str):
    """
    Load the json file
    """
    data = None

    if not os.path.exists(file):
        return data

    try:
        with open(file, "r") as file:
            data = json.load(file)
    except Exception as err:
        bt.logging.warning(f"Could not load the data from {file}: {err}")

    return data
