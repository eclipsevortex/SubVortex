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
import bittensor.core.axon as btca
from typing import Callable, Tuple

from subvortex.core.core_bittensor.synapse import Synapse


class SubVortexAxon(btca.Axon):
    def __init__(
        self,
        *args,
        blacklist_fn: Callable[[Synapse], Tuple[bool, str]] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # Remove the initial ping endpoint
        self.router.delete("/ping")

        # Attach new ping endpoint
        def ping(r: Synapse) -> Synapse:
            return r

        self.attach(
            forward_fn=ping, verify_fn=None, blacklist_fn=blacklist_fn, priority_fn=None
        )
