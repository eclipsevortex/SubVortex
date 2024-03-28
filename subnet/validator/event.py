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

from dataclasses import dataclass, asdict
from typing import List, Optional, Any


@dataclass
class EventSchema:
    successful: List[bool]  # List of whether or not the task was successful or not
    completion_times: List[float]  # List of completion times for a given task
    block: float  # Current block at given step
    uids: Optional[List[int]]  # Queried uids
    countries: Optional[List[int]]  # Queried countries
    step_length: float  # Elapsed time between the beginning of a run step to the end of a run step
    best_uid: str  # Best completion for given task
    best_hotkey: str  # Best hotkey for given task
    availability_scores: List[float]  # list of availability score
    latency_scores: List[float]  # list of latency score
    reliability_scores: List[float]  # list of reliability score
    distribution_scores: List[float]  # list of distribution score

    # Reward data
    rewards: Optional[List[float]]  # Reward vector for given step

    # Weights data and moving averages
    moving_averaged_scores: List[float] = None
