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

from subvortex.core.model.neuron import Neuron
from subvortex.validator.core.model.miner import Miner
from subvortex.validator.core.model.score import Score
from subvortex.validator.core.challenger.database import Database
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
        database: Database,
        step_index: int,
        challengees: typing.List[Neuron],
        results: typing.Dict[str, typing.List[ChallengeResult]],
    ):
        miners_by_hotkey: dict[str, Miner] = {}
        scores_by_hotkey: dict[str, dict[str, Score]] = {}
        scores_by_node_id: dict[str, Score] = {}

        # Load all scores from the database
        for challengee in challengees:
            # Load scores
            challengee_scores = await database.get_scores(challengee.hotkey)
            scores_by_hotkey[challengee.hotkey] = challengee_scores
            scores_by_node_id.update(challengee_scores)

            # Load miner
            miner = await database.get_miner(challengee.hotkey)
            miners_by_hotkey[challengee.hotkey] = miner

        # Evaluate challenge results and update scores
        for challengee in challengees:
            # Set variables
            uid = challengee.uid
            hotkey = challengee.hotkey

            # Get the result for each node owned by the challengee
            nodes_result = results.get(hotkey)

            if not nodes_result:
                btul.logging.warning(
                    f"[{step_index}][{uid}] Missing result. Assuming full failure.",
                    prefix=self.settings.logging_name,
                )
                self._apply_zero_score(challengee)
                continue

            # Get the scores for the challengee
            challengee_scores = scores_by_hotkey[hotkey]

            # Compute individual scores
            for node_result in nodes_result:
                btul.logging.debug(
                    f"[{step_index}][{uid}] Evaluating challenge result for: {hotkey}/{node_result.id}",
                    prefix=self.settings.logging_name,
                )

                score = challengee_scores.get(node_result.id)
                if not score:
                    score = Score(uid=uid, hotkey=hotkey, node_id=node_result.id)
                    challengee_scores[node_result.id] = score
                    scores_by_node_id[node_result.id] = score

                if not node_result.is_successful:
                    btul.logging.warning(
                        f"[{step_index}][{uid}] Challenge failed: {node_result.reason}",
                        prefix=self.settings.logging_name,
                    )

                # Refresh metadata from results
                score.availability_attempts, score.availability_successes = (
                    score_utils.refresh_availability_metadata(
                        settings=self.settings, result=nodes_result, score=score
                    )
                )
                score.reliability_attempts, score.reliability_successes = (
                    score_utils.refresh_reliability_metadata(
                        settings=self.settings, result=nodes_result, score=score
                    )
                )
                score.latency_times = score_utils.refresh_latency_metadata(
                    settings=self.settings, result=nodes_result, score=score
                )
                (
                    score.performance_attempts,
                    score.performance_successes,
                    score.performance_boost,
                ) = score_utils.refresh_performance_metadata(
                    settings=self.settings, result=nodes_result, score=score
                )

                # Compute availability and reliability scores
                score.availability_score = score_utils.compute_availability_score(score)
                score.reliability_score = score_utils.compute_reliability_score(score)

            # Compute collective scores
            for node_result in nodes_result:
                score = scores_by_node_id[node_result.id]
                score.latency_score = score_utils.compute_latency_score(
                    scores_by_node_id, score
                )
                score.performance_score = score_utils.compute_performance_score(
                    scores_by_node_id, score
                )

            # Compute global scores
            for node_result in nodes_result:
                score = scores_by_node_id[node_result.id]
                score.distribution_score = score_utils.compute_distribution_score(
                    self.settings, scores_by_node_id, score
                )
                score.score = score_utils.compute_final_score(self.settings, challengee)

        # Save scores in the database
        all_scores = list(scores_by_node_id.values())
        await database.save_scores(scores=all_scores)

        # Compute the challengees scores
        for challengee in challengees:
            # Get the miner
            miner = miners_by_hotkey.get(challengee.hotkey)

            # Get all the scores
            scores = scores_by_hotkey.get(challengee.hotkey)

            # Compute the miner score
            miner.score = score_utils.compute_miner_score(scores)

            # Compute moving score
            miner.moving_score = (
                self.settings.moving_score_alpha * miner.score
                + (1 - self.settings.moving_score_alpha) * miner.moving_score
            )

        # Save miners in the database
        all_miners = list(miners_by_hotkey.values())
        await database.update_miners(miners=all_miners)

    def _apply_zero_score(self, score: Score):
        score.availability_score = 0.0
        score.reliability_score = 0.0
        score.latency_score = 0.0
        score.performance_score = 0.0
        score.distribution_score = 0.0
        score.score = 0.0
