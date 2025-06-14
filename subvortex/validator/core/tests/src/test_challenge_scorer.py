# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex

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
import pytest
from unittest.mock import patch
from subvortex.validator.core.challenger.challenge_scorer import ChallengeScorer
from subvortex.validator.core.challenger.model import ChallengeResult
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.model.miner import Miner


@pytest.fixture
def settings():
    s = Settings.create()
    s.logging_name = "test"
    return s


@pytest.fixture
def successful_result():
    return ChallengeResult.create_default(
        chain="bittensor", type="lite", is_available=True, is_reliable=True
    )


@pytest.fixture
def failed_result():
    return ChallengeResult.create_failed(
        reason="timeout", challenge_attempts=1, avg_process_time=5
    )


@pytest.fixture
def miners():
    return [
        Miner(uid=1, hotkey="hk1", ip="1.1.1.1", country="US"),
        Miner(uid=2, hotkey="hk2", ip="1.1.1.2", country="US"),
    ]


@pytest.mark.asyncio
async def test_score_all_successful(settings, miners, successful_result):
    results = {m.hotkey: successful_result for m in miners}
    scorer = ChallengeScorer(settings)

    with patch(
        "subvortex.validator.core.challenger.score.refresh_availability_metadata"
    ) as avail, patch(
        "subvortex.validator.core.challenger.score.refresh_reliability_metadata"
    ) as reliab, patch(
        "subvortex.validator.core.challenger.score.refresh_latency_metadata"
    ) as latency, patch(
        "subvortex.validator.core.challenger.score.refresh_performance_metadata"
    ) as perf, patch(
        "subvortex.validator.core.challenger.score.compute_availability_score"
    ) as avs, patch(
        "subvortex.validator.core.challenger.score.compute_reliability_score"
    ) as rs, patch(
        "subvortex.validator.core.challenger.score.compute_latency_score"
    ) as ls, patch(
        "subvortex.validator.core.challenger.score.compute_performance_score"
    ) as ps, patch(
        "subvortex.validator.core.challenger.score.compute_distribution_score"
    ) as ds, patch(
        "subvortex.validator.core.challenger.score.compute_final_score"
    ) as fs:

        avail.return_value = (1, 1)
        reliab.return_value = (1, 1)
        latency.return_value = [0.1]
        perf.return_value = (1, 1, 0.0)
        avs.return_value = 1.0
        rs.return_value = 1.0
        ls.return_value = 1.0
        ps.return_value = 1.0
        ds.return_value = 1.0
        fs.return_value = 1.0

        await scorer.run(step_index=0, challengees=miners, results=results)

        for m in miners:
            assert m.score == 1.0
            assert 0.0 <= m.moving_score <= 1.0


@pytest.mark.asyncio
async def test_score_some_missing_results(settings, miners, successful_result):
    results = {"hk1": successful_result}
    scorer = ChallengeScorer(settings)

    with patch(
        "subvortex.validator.core.challenger.score.refresh_availability_metadata"
    ) as avail, patch(
        "subvortex.validator.core.challenger.score.refresh_reliability_metadata"
    ) as reliab, patch(
        "subvortex.validator.core.challenger.score.refresh_latency_metadata"
    ) as latency, patch(
        "subvortex.validator.core.challenger.score.refresh_performance_metadata"
    ) as perf, patch(
        "subvortex.validator.core.challenger.score.compute_availability_score"
    ) as avs, patch(
        "subvortex.validator.core.challenger.score.compute_reliability_score"
    ) as rs, patch(
        "subvortex.validator.core.challenger.score.compute_latency_score"
    ) as ls, patch(
        "subvortex.validator.core.challenger.score.compute_performance_score"
    ) as ps, patch(
        "subvortex.validator.core.challenger.score.compute_distribution_score"
    ) as ds, patch(
        "subvortex.validator.core.challenger.score.compute_final_score"
    ) as fs:

        avail.return_value = (1, 1)
        reliab.return_value = (1, 1)
        latency.return_value = [0.2]
        perf.return_value = (1, 1, 0.1)
        avs.return_value = 0.9
        rs.return_value = 0.9
        ls.return_value = 0.9
        ps.return_value = 0.9
        ds.return_value = 0.9
        fs.return_value = 0.9

        await scorer.run(step_index=1, challengees=miners, results=results)

        assert miners[0].score == 0.9
        assert miners[1].score == 0.0


@pytest.mark.asyncio
async def test_score_failure_result(settings, miners, failed_result):
    results = {miners[0].hotkey: failed_result}
    scorer = ChallengeScorer(settings)

    with patch(
        "subvortex.validator.core.challenger.score.refresh_availability_metadata"
    ) as avail, patch(
        "subvortex.validator.core.challenger.score.refresh_reliability_metadata"
    ) as reliab, patch(
        "subvortex.validator.core.challenger.score.refresh_latency_metadata"
    ) as latency, patch(
        "subvortex.validator.core.challenger.score.refresh_performance_metadata"
    ) as perf, patch(
        "subvortex.validator.core.challenger.score.compute_availability_score"
    ) as avs, patch(
        "subvortex.validator.core.challenger.score.compute_reliability_score"
    ) as rs, patch(
        "subvortex.validator.core.challenger.score.compute_latency_score"
    ) as ls, patch(
        "subvortex.validator.core.challenger.score.compute_performance_score"
    ) as ps, patch(
        "subvortex.validator.core.challenger.score.compute_distribution_score"
    ) as ds, patch(
        "subvortex.validator.core.challenger.score.compute_final_score"
    ) as fs:

        avail.return_value = (1, 0)
        reliab.return_value = (1, 0)
        latency.return_value = []
        perf.return_value = (1, 0, 0.0)
        avs.return_value = 0.0
        rs.return_value = 0.0
        ls.return_value = 0.0
        ps.return_value = 0.0
        ds.return_value = 0.0
        fs.return_value = 0.0

        await scorer.run(step_index=2, challengees=miners[:1], results=results)

        m = miners[0]
        assert m.score == 0.0
        assert m.availability_score == 0.0
        assert m.reliability_score == 0.0
