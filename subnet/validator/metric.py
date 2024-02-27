import typing
import torch
import bittensor as bt

from subnet.validator.utils import get_available_query_miners
from subnet.validator.reward import apply_reward_scores

metric2_rewards = {1: 1, 2: 0.75, 3: 0.5, 4: 0.25}
metric3_rewards: typing.List = [
    {"min": 2, "max": 5, "value": 0.25},
    {"min": 5, "max": 10, "value": 0.5},
    {"min": 10, "max": 15, "value": 0.75},
    {"min": 20, "value": 1},
]


async def compute_metrics(self):
    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"compute metrics uids {uids}")

    # Compute the rewards for the responses given the prompt.
    rewards: torch.FloatTensor = torch.zeros(len(uids), dtype=torch.float32).to(
        self.device
    )

    process_times = []
    for idx, uid in enumerate(uids):
        axon = self.metagraph.axons[idx]

        # Get the coldkey
        coldkey = axon.coldkey

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Update subtensor statistics in the subs hash
        subs_key = f"subs:{coldkey}:{hotkey}"

        # Get all the keys owned by the coldkey
        keys_cached = await self.database.keys(f"subs:{coldkey}:*")

        # Metric 1 - Ownership: Subtensor and miner have to be on the same machine
        subtensor_ip = await self.database.hget(subs_key, "ip")
        metric1 = 1 * (1 if axon.ip == subtensor_ip else 0)
        bt.logging.debug(f"[Metric 1] Ownership {metric1}")

        # Metric 2 - Unicity: One subtensor linked to one miner
        miners = []
        for key in keys_cached:
            ip = await self.database.hget(subs_key, "ip")
            if subtensor_ip == ip:
                miners.append(key)

        number_of_miners = len(miners)
        metric2 = 1 * (metric2_rewards.get(number_of_miners) or 0)
        bt.logging.debug(f"[Metric 2] Unicity {metric2}")

        # Metric 3 - Diversity: Maximise subtensors's timezone owned by a coldkey
        timezones = []
        for key in keys_cached:
            timezone = await self.database.hget(key, "timezone")
            if timezone not in timezones:
                timezones.append(key)

        number_of_timezone = len(timezones)
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
        bt.logging.debug(f"[Metric 3] Diversity {metric3}")

        # Apply reward for this challenge
        rewards[idx] = (metric1 + metric2 + metric3) / 3
        bt.logging.debug(f"Rewards {rewards[idx]}")

        # Get the process time for each uid to apply the rewards accordingly
        process_time = await self.database.hget(key, "process_time")
        process_times.append(float(process_time))

    if len(rewards) == 0:
        return

    bt.logging.trace("Applying challenge rewards")
    apply_reward_scores(
        self,
        uids=uids,
        process_times=process_times,
        rewards=rewards,
        timeout=30,
    )
