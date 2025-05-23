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
import os
import json
import bittensor.utils.btlogging as btul

from subvortex.core.shared.encoder import EnumEncoder


def save_json_file(file: str, items):
    """
    Save the items in a json file
    """
    try:
        with open(file, "w") as file:
            data = json.dumps(items, indent=4, cls=EnumEncoder)
            file.write(data)
    except Exception as err:
        btul.logging.warning(f"Could not save the data in {file}: {err}")


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
        btul.logging.warning(f"Could not load the data from {file}: {err}")

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
        btul.logging.warning(f"Could not load the data from {file}: {err}")

    return data
