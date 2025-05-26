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


def load_request_log(request_log_path: str) -> dict:
    """
    Loads the request logger from disk if it exists.

    Args:
        log_path (str): The path to the directory containing the request log.

    Returns:
        Dict: The request log data, if it exists, or an empty dictionary.

    This method loads the request log from disk if it exists. If not, it returns an empty dictionary.
    """
    if os.path.exists(request_log_path):
        try:
            with open(request_log_path, "r") as f:
                request_log = json.load(f)
        except Exception as e:
            btul.logging.error(f"Error loading request log: {e}. Resetting.")
            request_log = {}
    else:
        request_log = {}
    return request_log
