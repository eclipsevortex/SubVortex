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

from subnet.constants import RELIABILLITY_RESET
from subnet.shared.subtensor import get_current_block
from subnet.validator.challenge import challenge_data
from subnet.validator.miner import reset_reliability_score


async def forward(self):
    btul.logging.info(f"forward step: {self.step}")

    # Record forward time
    start = time.time()

    # Send synapse to get challenge
    btul.logging.info("initiating challenge")
    await challenge_data(self)

    # Reset reliability statistics every 3 epochs
    if get_current_block(self.subtensor) % RELIABILLITY_RESET == 0 and self.step > 0:
        await reset_reliability_score(self, self.miners)

    # Display step time
    forward_time = time.time() - start
    btul.logging.info(f"forward step time: {forward_time:.2f}s")
