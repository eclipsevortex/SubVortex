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
import re
from collections import defaultdict


def get(data, key: str, default=None):
    """
    Recursively fetches a value from a nested dictionary.

    :param d: The dictionary to search.
    :param keys: A list of keys representing the path to the value.
    :param default: The default value to return if the key is not found.
    :return: The value if found, else the default value.
    """
    keys = key.split(".")
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def decode(payload, encoding: str = "utf-8"):
    try:
        content = payload.decode(encoding) if isinstance(payload, bytes) else payload
        return content
    except Exception:
        return ""


def extract_and_transform_headers(payload):
    # Split the request into lines
    lines = payload.split("\n")

    # Initialize a dictionary to store the headers
    headers = {}

    # Regular expression to match key-value pairs
    header_regex = re.compile(r"^(.*?):\s*(.*)$")

    for line in lines:
        # Skip empty lines and the first request line (e.g., POST /Synapse HTTP/1.1)
        if line and not line.startswith(("POST", "GET", "HTTP")):
            match = header_regex.match(line)
            if match:
                key, value = match.groups()
                # Remove "bt_header_" prefix if it exists
                key = key.replace("bt_header_", "")

                if (
                    key.endswith("_version")
                    or key.endswith("_port")
                    or key.endswith("_nonce")
                ):
                    headers[key] = int(value.strip()) if value else 0
                else:
                    headers[key] = value.strip()

    return headers


def clean_sources_2(id, sources, current_time, max_time):
    changed = False
    new_sources = defaultdict(list)
    sources_outdated = defaultdict(list)

    sources_dumped = dict.copy(sources)
    for id, source in sources_dumped.items():
        for request in source:
            if current_time - request.current_time <= max_time:
                new_sources[id].append(request)
            else:
                sources_outdated[id].append(request)
                changed = True

        if not any(x.is_denied() or x.is_allowed() for x in new_sources[id]):
            found = next(
                (
                    x
                    for x in sources_outdated[id][::-1]
                    if x.is_denied() or x.is_allowed()
                ),
                None,
            )
            if found:
                new_sources[id] = [found] + new_sources[id]

    return new_sources, changed


def clean_sources(sources, current_time):
    new_source = defaultdict(list)
    old_sources = defaultdict(list)
    found = None

    for id, source in sources.items():
        found = None
        for x in source:
            if current_time - x.current_time <= x.max_time:
                new_source[id].append(x)
            else:
                old_sources[id].append(x)
                if x.is_denied() or x.is_allowed():
                    found = x

        if not any(x.is_denied() or x.is_allowed() for x in new_source[id]) and found:
            new_source[id].insert(0, found)
            old_sources[id].remove(found)

        # Update the previous links
        previous_id = None
        for index, request in enumerate(new_source[id]):
            if index == 0:
                # First request as no previous request
                request.previous_id = None
                continue

            if index == 1 or request.previous_id == previous_id:
                # Second request or any request that has the same previous
                # as the second request have to change it to the new first request
                previous_id = request.previous_id
                request.previous_id = new_source[id][0].id
                continue

            break

    return old_sources, new_source
