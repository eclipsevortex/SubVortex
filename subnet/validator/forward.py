# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 philanthrope

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

import time
import bittensor as bt

from pprint import pformat
from .network import monitor

from subnet.validator.rebalance import rebalance_data
from subnet.validator.state import save_state, log_event
from subnet.validator.utils import get_current_epoch
from subnet.validator.bonding import compute_all_tiers
from subnet.validator.subtensor import subtensor_data
from subnet.validator.challenge import challenge_data
from subnet.validator.metrics import metrics_data
from subnet.validator.metric import compute_metrics
from subnet.validator.database import (
    get_miner_statistics,
    purge_expired_ttl_keys,
    purge_challenges_for_all_hotkeys,
)


async def forward(self):
    bt.logging.info(f"forward step: {self.step}")

    # Record forward time
    start = time.time()

    if self.step == 0:
        # Send synapse to get Subtensor details
        bt.logging.info("initiating subtensor")
        await subtensor_data(self)
    
    if self.step % 100 == 0:
        # Send synapse to get some metrics
        bt.logging.info("initiating metrics")
        await metrics_data(self)

    # Send synapse to challenge the miner
    bt.logging.info("initiating challenge")
    await challenge_data(self)

    # Compute the metrics
    await compute_metrics(self)

    # Monitor every step
    down_uids = await monitor(self)
    if len(down_uids) > 0:
        bt.logging.info(f"Downed uids marked for rebalance: {down_uids}")
        await rebalance_data(
            self,
            k=2,  # increase redundancy
            dropped_hotkeys=[self.metagraph.hotkeys[uid] for uid in down_uids],
            hotkey_replaced=False,  # Don't delete challenge data (only in subscription handler)
        )

    # Purge all challenge data to start fresh and avoid requerying hotkeys with stale challenge data
    current_epoch = get_current_epoch(self.subtensor, self.config.netuid)
    bt.logging.info(
        f"Current epoch: {current_epoch} | Last purged epoch: {self.last_purged_epoch}"
    )
    if current_epoch % 10 == 0:
        if self.last_purged_epoch < current_epoch:
            bt.logging.info("initiating challenges purge")
            await purge_challenges_for_all_hotkeys(self.database)
            self.last_purged_epoch = current_epoch
            save_state(self)

    # Purge expired TTL keys
    if self.step % 60 == 0:
        bt.logging.info("initiating TTL purge for expired keys")
        await purge_expired_ttl_keys(self.database)

    # Compute tiers and stats
    if self.step % 360 == 0 and self.step > 0:
        bt.logging.info("initiating compute stats")
        await compute_all_tiers(self.database)

        # Update miner statistics and usage data.
        stats = await get_miner_statistics(self.database)
        bt.logging.debug(f"miner stats: {pformat(stats)}")

    # Display step time
    forward_time = time.time() - start
    bt.logging.info(f"forward step time: {forward_time:.2f}s")
