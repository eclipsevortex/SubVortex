# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

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

import torch
from typing import List
from template.utils.subtensor import Subtensor
from template.utils.miner import Miner

metric2_rewards = {1: 1, 2: 0.75, 3: 0.5, 4: 0.25}
metric3_rewards: List = [
    {"min": 2, "max": 5, "value": 0.25},
    {"min": 5, "max": 10, "value": 0.5},
    {"min": 10, "max": 15, "value": 0.75},
    {"min": 20, "value": 1},
]


def find_miner(miners: List[Miner], uid: torch.Tensor):
    result = next((i for i, obj in enumerate(miners) if obj.uid == uid), None)
    return result is not None


def reward(uid: str, subtensors: List[Subtensor]) -> float:
    """
    Reward the miner response to the dummy request. This method returns a reward
    value for the miner, which is used to update the miner's score.

    Returns:
    - float: The reward value for the miner.
    """

    subtensor_index = next(
        (i for i, obj in enumerate(subtensors) if find_miner(obj.miners, uid)), None
    )
    if subtensor_index is None:
        return 0

    subtensor = subtensors[subtensor_index]
    miner = next(
        (obj for i, obj in enumerate(subtensor.miners) if obj.uid == uid), None
    )

    # Metric 1 - Subtensor and miner on different machine
    metric1 = 1 * (1 if miner.ip != subtensor.ip else 0)

    # Metric 2 - Max reward if one miner == one subtensor
    number_of_miners = len(subtensor.miners)
    metric2 = 1 * (metric2_rewards[number_of_miners] or 0)

    # Metric 3 - Coldkey maximise location diversity
    subtensors_owned = [
        item for item in subtensors if item.cold_key == subtensor.cold_key
    ]
    number_of_timezone = len({item.timezone for item in subtensors_owned})
    metric3_reward = next(
        (
            obj
            for i, obj in enumerate(metric3_rewards)
            if obj["min"] <= number_of_timezone
            and (obj["max"] is None or number_of_timezone < obj["max"])
        ),
        None,
    )
    metric3 = 1 * (metric3_reward["value"] if metric3_reward is not None else 0)

    # Metric 4 - Subtensor behind VPS

    # Metric 5 - Availability computed over 7 days - need a database

    # Metric 6 - Performance

    # Metrix X - Check miner owns the subtensor (when miner and subtensor are not on the same machine)

    print(f"[{uid}] M1: {metric1}, M2: {metric2}, M3: {metric3}")

    return (metric1 + metric2 + metric3) / 3


def get_rewards(
    self,
    uids: torch.LongTensor,
    subtensors: List[Subtensor],
) -> torch.FloatTensor:
    """
    Returns a tensor of rewards for the given query and responses.

    Args:
    - query (int): The query sent to the miner.
    - responses (List[float]): A list of responses from the miner.

    Returns:
    - torch.FloatTensor: A tensor of rewards for the given query and responses.
    """
    # Get all the reward results by iteratively calling your reward() function.
    return torch.FloatTensor([reward(uid, subtensors) for uid in uids]).to(self.device)
