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

import math
import bittensor as bt

from subnet.constants import *
from subnet.validator.miner import Miner
from subnet.validator.database import update_hotkey_statistics


def wilson_score_interval(successes, total):
    if total == 0:
        return 0.5  # chance

    z = 0.6744897501960817

    p = successes / total
    denominator = 1 + z**2 / total
    centre_adjusted_probability = p + z**2 / (2 * total)
    adjusted_standard_deviation = math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)

    lower_bound = (
        centre_adjusted_probability - z * adjusted_standard_deviation
    ) / denominator
    upper_bound = (
        centre_adjusted_probability + z * adjusted_standard_deviation
    ) / denominator

    wilson_score = (max(0, lower_bound) + min(upper_bound, 1)) / 2

    bt.logging.trace(
        f"Wilson score interval with {successes} / {total}: {wilson_score}"
    )
    return wilson_score


async def update_statistics(
    self,
    miner: Miner,
):
    '''
    Update the statistics of the miner in the database
    '''
    # Get the hotkey
    hotkey = self.metagraph.hotkeys[miner.uid]

    # Update statistics
    await update_hotkey_statistics(hotkey, miner.snapshot, self.database)
