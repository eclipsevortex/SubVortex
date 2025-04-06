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
import time
import bittensor.utils.btlogging as btul
from os import path

# Check if there is an update every 5 minutes
# Github Rate Limit 60 requests per hour / per ip (Reference: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28)
CHECK_UPDATE_FREQUENCY = 5 * 60

here = path.abspath(path.dirname(__file__))


def should_upgrade(auto_update: bool, last_upgrade_check: float):
    """
    True if it is time to upgrade, false otherwise
    """
    time_since_last_update = time.time() - last_upgrade_check
    return time_since_last_update >= CHECK_UPDATE_FREQUENCY and auto_update


def load_json_file(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r") as file:
            config = json.load(file)
        return config
    except Exception:
        btul.logging.warning(f"Could not load the json file {file_path}")
