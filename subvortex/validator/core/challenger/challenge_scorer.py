# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import typing
import bittensor.utils.btlogging as btul

from subvortex.validator.core.model.miner import Miner
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.challenger.model import ChallengeResult
import subvortex.validator.core.challenger.score as score_utils


class ChallengeScorer:
    """
    Applies scoring to miners after a challenge execution. This includes:
    - Updating availability, reliability, latency, and performance metadata
    - Computing all relevant scores
    - Logging scores for observability
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(
        self,
        step_index: int,
        challengees: typing.List[Miner],
        results: typing.Dict[str, ChallengeResult],
    ):
        for miner in challengees:
            result = results.get(miner.hotkey)
            uid = miner.uid
            hotkey = miner.hotkey

            btul.logging.debug(
                f"[{step_index}][{uid}] Evaluating challenge result for: {hotkey}",
                prefix=self.settings.logging_name,
            )

            if not result:
                btul.logging.warning(
                    f"[{step_index}][{uid}] Missing result. Assuming full failure.",
                    prefix=self.settings.logging_name,
                )
                self._apply_zero_score(miner)
                self._update_moving_score(miner, step_index, uid)
                continue

            if not result.is_successful:
                btul.logging.warning(
                    f"[{step_index}][{uid}] Challenge failed: {result.reason}",
                    prefix=self.settings.logging_name,
                )

            # --- Refresh miner metadata from result ---
            miner.availability_attempts, miner.availability_successes = (
                score_utils.refresh_availability_metadata(self.settings, result, miner)
            )
            miner.reliability_attempts, miner.reliability_successes = (
                score_utils.refresh_reliability_metadata(self.settings, result, miner)
            )
            miner.latency_times = score_utils.refresh_latency_metadata(
                self.settings, result, miner
            )
            (
                miner.performance_attempts,
                miner.performance_successes,
                miner.performance_boost,
            ) = score_utils.refresh_performance_metadata(self.settings, result, miner)

            # --- Compute all scores ---
            miner.availability_score = score_utils.compute_availability_score(miner)
            miner.reliability_score = score_utils.compute_reliability_score(miner)
            miner.latency_score = score_utils.compute_latency_score(challengees, miner)
            miner.performance_score = score_utils.compute_performance_score(
                challengees, miner
            )
            miner.distribution_score = score_utils.compute_distribution_score(
                self.settings, miner, challengees
            )
            miner.score = score_utils.compute_final_score(self.settings, miner)

            # --- Update moving average ---
            self._update_moving_score(miner, step_index, uid)

    def _apply_zero_score(self, miner: Miner):
        miner.availability_score = 0.0
        miner.reliability_score = 0.0
        miner.latency_score = 0.0
        miner.performance_score = 0.0
        miner.distribution_score = 0.0
        miner.score = 0.0

    def _update_moving_score(self, miner: Miner, step_index: int, uid: int):
        miner.moving_score = (
            self.settings.moving_score_alpha * miner.score
            + (1 - self.settings.moving_score_alpha) * miner.moving_score
        )
        btul.logging.info(
            f"[{step_index}][{uid}] Score: {miner.score:.4f}, Moving: {miner.moving_score:.4f}",
            prefix=self.settings.logging_name,
        )
