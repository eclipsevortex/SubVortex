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

import typing
import bittensor as bt


class Score(bt.Synapse):
    validator_uid: typing.Optional[int]
    # True if the miner is the primary, false otherwise 
    primary: typing.Optional[bool]
    # True if the miner/subtensor are up, false otherwise
    verified: typing.Optional[bool]
    # Reason of the why it is not verified
    reason: typing.Optional[str]
    availability: float
    latency: float
    reliability: float
    distribution: float
    score: float

    # Deprecated - wont be send by validators anymore
    count: typing.Optional[int] = 0

    # Returns
    version: typing.Optional[str] = None

    def deserialize(self) -> typing.Optional[str]:
        return self.version