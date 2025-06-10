# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex

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
from collections import Counter

import bittensor.utils.btlogging as btul

from subvortex.core.model.challenge import Challenge
from subvortex.validator.core.model.miner import Miner
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.challenger.model import ChallengeResult
from subvortex.validator.core.challenger.challenges.executor import execute_challenge


class ChallengeExecutor:
    """
    Responsible for filtering out invalid challengees (e.g. IP collision, missing identity),
    then executing the challenge using the underlying executor.
    """

    def __init__(self, settings: Settings, subtensor):
        self.settings = settings
        self.subtensor = subtensor

    async def run(
        self,
        step_id: str,
        step_index: int,
        challengees: typing.List[Miner],
        identities: typing.Dict[str, typing.List],
        ip_counts: Counter,
    ) -> typing.Tuple[typing.Dict[str, ChallengeResult], Challenge]:
        checks_result: typing.Dict[str, ChallengeResult] = {}

        # --- Filter out invalid challengees ---
        for miner in challengees:
            hotkey = miner.hotkey
            ip = miner.ip

            # Validate identity presence
            if hotkey not in identities:
                checks_result[hotkey] = ChallengeResult.create_failed(
                    reason="Identity is not set",
                    challenge_attempts=self.settings.default_challenge_max_iteration,
                    avg_process_time=self.settings.challenge_timeout,
                )
                btul.logging.debug(
                    f"[{step_index}][{miner.uid}] Skipped - identity not found",
                    prefix=self.settings.logging_name,
                )
                continue

            # Validate unique IP usage
            if ip_counts[ip] > 1:
                checks_result[hotkey] = ChallengeResult.create_failed(
                    reason=f"{ip_counts[ip]} miners share IP {ip}",
                    challenge_attempts=self.settings.default_challenge_max_iteration,
                    avg_process_time=self.settings.challenge_timeout,
                )
                btul.logging.debug(
                    f"[{step_index}][{miner.uid}] Skipped - IP conflict ({ip})",
                    prefix=self.settings.logging_name,
                )

        # --- Prepare list of miners to challenge ---
        valid_challengees = [x for x in challengees if x.hotkey not in checks_result]

        if not valid_challengees:
            btul.logging.warning(
                f"[{step_index}] No valid miners found for challenge.",
                prefix=self.settings.logging_name,
            )
            return checks_result, None

        # --- Execute the challenge ---
        btul.logging.info(
            f"[{step_index}] Executing challenge on {len(valid_challengees)} miners",
            prefix=self.settings.logging_name,
        )
        challenge_results, challenge = await execute_challenge(
            step_id=step_id,
            settings=self.settings,
            subtensor=self.subtensor,
            challengers=valid_challengees,
            nodes=identities,
        )

        # --- Merge filtered and executed results ---
        full_results = {**checks_result, **challenge_results}

        return full_results, challenge
