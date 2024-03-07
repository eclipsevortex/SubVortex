import typing
import torch
import bittensor as bt

from subnet.constants import METRIC_FAILURE_REWARD
from subnet.validator.utils import get_available_query_miners
from subnet.validator.bonding import (
    register_miner,
    miner_is_registered,
    get_tier_factor,
)

metric2_rewards = {1: 1, 2: 0.75, 3: 0.5, 4: 0.25}
metric3_rewards: typing.List = [
    {"min": 2, "max": 5, "value": 0.25},
    {"min": 5, "max": 10, "value": 0.5},
    {"min": 10, "max": 15, "value": 0.75},
    {"min": 20, "value": 1},
]
metric4_rewards: typing.List = [
    {"min": 0, "max": 1, "value": 1},
    {"min": 1, "max": 2, "value": 0.75},
    {"min": 2, "max": 3, "value": 0.5},
    {"min": 3, "value": 0},
]


async def compute_rewards(self, verification):
    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"compute metrics uids {uids}")

    # Compute the rewards for the responses given the prompt.
    rewards: torch.FloatTensor = torch.zeros(len(uids), dtype=torch.float32).to(
        self.device
    )

    for idx, uid in enumerate(uids):
        axon = self.metagraph.axons[idx]

        # Get the coldkey
        coldkey = axon.coldkey

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Subtensor info key
        subs_key = f"subs:{coldkey}:{hotkey}"

        # Get all the keys owned by the coldkey
        keys_cached = await self.database.keys(f"subs:{coldkey}:*")

        # Check and see if this miner is registered.
        if not await miner_is_registered(hotkey, self.database):
            bt.logging.debug(f"[Metric][{uid}] Registering new miner {hotkey}...")
            await register_miner(hotkey, self.database)

        # Miner statistics key
        stats_key = f"stats:{hotkey}"

        subtensor_ip = await self.database.hget(subs_key, "ip")

        # # Metric 1 - Ownership: Subtensor and miner have to be on the same machine
        # metric1 = 1 * (1 if axon.ip == subtensor_ip else 0)
        # await self.database.hset(stats_key, f"ownership", metric1)
        # bt.logging.debug(f"[Metric][{uid}][#1] Ownership {metric1}")

        # Metric 2 - Unicity: One subtensor linked to one miner
        miners = []
        for key in keys_cached:
            ip = await self.database.hget(subs_key, "ip")
            if subtensor_ip == ip:
                miners.append(key)

        number_of_miners = len(miners)
        metric2 = 1 * (metric2_rewards.get(number_of_miners) or 0)
        await self.database.hset(stats_key, f"unicity", metric2)
        bt.logging.debug(f"[Metric][{uid}][#2] Unicity {metric2}")

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
                for obj in metric3_rewards
                if obj["min"] <= number_of_timezone
                and (obj["max"] is None or number_of_timezone < obj["max"])
            ),
            None,
        )
        metric3 = 1 * (metric3_reward["value"] if metric3_reward is not None else 0)
        await self.database.hset(stats_key, f"diversity", metric3)
        bt.logging.debug(f"[Metric][{uid}][#3] Diversity {metric3}")

        # Metric 4 - Latency: Maximise the best time
        latency = await self.database.hget(subs_key, "latency")
        metric4_reward = next(
            (
                obj
                for obj in metric3_rewards
                if obj["min"] <= latency
                and (obj["max"] is None or number_of_timezone < obj["max"])
            ),
            None,
        )
        metric4 = 1 * (metric4_reward["value"] if metric4_reward is not None else 0)
        await self.database.hset(stats_key, f"latency", metric4)
        bt.logging.debug(f"[Metric][{uid}][#4] Latency {metric4}")

        # Get the tier factor
        tier_factor = await get_tier_factor(hotkey, self.database)

        # Apply reward for this challenge
        rewards[idx] = ((metric2 + metric3 + metric4) / 3) * tier_factor if verification[idx] else METRIC_FAILURE_REWARD
        bt.logging.debug(f"[Metric][{uid}] Rewards {rewards[idx]}")

    return rewards
