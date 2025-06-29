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

from subvortex.core.core_bittensor.synapse import Synapse


class Score(Synapse):
    validator_uid: typing.Optional[int] = None
    block: typing.Optional[int] = None
    rank: typing.Optional[int] = None
    availability: float
    latency: float
    reliability: float
    distribution: float
    score: float
    moving_score: typing.Optional[float] = 0
    count: typing.Optional[int] = 0
    penalty_factor: typing.Optional[float] = None
    reason: typing.Optional[str] = None
    detail: typing.Optional[str] = None

    # Returns
    version: typing.Optional[str] = None

    def deserialize(self) -> typing.Optional[str]:
        return self.version
