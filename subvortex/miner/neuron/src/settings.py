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
from dotenv import load_dotenv
from dataclasses import dataclass, field

import subvortex.core.settings_utils as scsu

load_dotenv()


@dataclass
class Settings:
    logging_name: str = field(default="Neuron", metadata={"readonly": True})
    """
    Prefix to use when logging
    """

    key_prefix: str = field(default="sv", metadata={"readonly": True})
    """
    Prefix to use for each key of the storage
    """

    netuid: int = 7
    """
    UID of the subnet
    """

    metagraph_sync_interval: int = 100
    """
    Interval the metagraph is forced to resync
    """

    database_host: str = "localhost"
    """
    Host of the redis instance
    """

    database_port: int = 6379
    """
    Port of the redis instance
    """

    database_index: int = 0
    """
    Index of the redis instance
    """

    database_password: str = None
    """
    Password of the redis instance
    """

    score_saving_enabled: bool = False
    """
    Whether to save the scores returned by the forward method
    """

    score_max_entries: int = 100
    """
    Maximum number of scores to keep (in file or Redis)
    """

    score_saving_target: str = "json"
    """
    Where to save the scores — options are 'json' or 'redis'
    """

    score_saving_json_path: str = None
    """
    Path to save the scores if using json
    """

    @classmethod
    def create(cls) -> "Settings":
        return scsu.create_settings_instance(cls)
