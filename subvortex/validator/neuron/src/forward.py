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
import time
import bittensor.utils.btlogging as btul

from subvortex.core.constants import RELIABILLITY_RESET
from subvortex.core.shared.subtensor import get_current_block
from subvortex.core.core_bittensor.subtensor import get_next_block
from subvortex.validator.neuron.src.challenge import challenge_data
from subvortex.validator.neuron.src.miner import reset_reliability_score


async def forward(self):
    # Display start of task
    current_block = get_next_block(subtensor=self.subtensor)
    btul.logging.info(f"Step #{self.step} starting at block #{current_block}")

    # Record forward time
    start = time.time()

    # Send synapse to get challenge
    await challenge_data(self, current_block)

    # Reset reliability statistics every 3 epochs
    if get_current_block(self.subtensor) % RELIABILLITY_RESET == 0 and self.step > 0:
        await reset_reliability_score(database=self.database, miners=self.miners)

    # Display end of task
    forward_time = time.time() - start
    current_block = get_next_block(subtensor=self.subtensor)
    btul.logging.info(f"Step finished at block #{current_block} in {forward_time:.2f}s")
