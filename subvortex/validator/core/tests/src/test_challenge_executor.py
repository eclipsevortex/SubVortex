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
from unittest.mock import AsyncMock, patch
from collections import Counter

from subvortex.validator.core.challenger.challenge_executor import ChallengeExecutor
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.challenger.model import ChallengeResult
from subvortex.validator.core.model.miner import Miner


@pytest.fixture
def settings():
    s = Settings.create()
    s.logging_name = "test"
    return s


@pytest.fixture
def dummy_miners():
    return [
        Miner(uid=1, hotkey="hk1", ip="1.1.1.1", country="US"),
        Miner(uid=2, hotkey="hk2", ip="1.1.1.2", country="US"),
        Miner(uid=3, hotkey="hk3", ip="1.1.1.1", country="US"),  # Duplicate IP
    ]


@pytest.mark.asyncio
async def test_all_valid_miners(settings, dummy_miners):
    identities = {
        "hk1": [{"chain": "bittensor", "type": "lite", "max-connection": 64}],
        "hk2": [{"chain": "bittensor", "type": "archive", "max-connection": 64}],
    }
    ip_counts = Counter(m.ip for m in dummy_miners[:2])
    mock_subtensor = AsyncMock()
    executor = ChallengeExecutor(settings, mock_subtensor)

    with patch("subvortex.validator.core.challenger.challenge_executor.execute_challenge") as mock_exec:
        mock_exec.return_value = (
            {
                "hk1": ChallengeResult.create_default(chain="bittensor", type="lite", is_available=True, is_reliable=True),
                "hk2": ChallengeResult.create_default(chain="bittensor", type="archive", is_available=True, is_reliable=True),
            },
            "challenge_obj",
        )

        results, challenge = await executor.run(
            step_index=0,
            challengees=dummy_miners[:2],
            identities=identities,
            ip_counts=ip_counts,
        )

        assert all(r.is_successful for r in results.values())
        assert challenge == "challenge_obj"
        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_miner_missing_identity(settings, dummy_miners):
    identities = {
        "hk1": [{"chain": "bittensor", "type": "lite", "max-connection": 64}],
    }
    ip_counts = Counter(m.ip for m in dummy_miners[:2])
    mock_subtensor = AsyncMock()
    executor = ChallengeExecutor(settings, mock_subtensor)

    with patch("subvortex.validator.core.challenger.challenge_executor.execute_challenge") as mock_exec:
        mock_exec.return_value = (
            {
                "hk1": ChallengeResult.create_default(chain="bittensor", type="lite", is_available=True, is_reliable=True),
            },
            "challenge_obj",
        )

        results, challenge = await executor.run(
            step_index=1,
            challengees=dummy_miners[:2],
            identities=identities,
            ip_counts=ip_counts,
        )

        assert "hk2" in results
        assert not results["hk2"].is_successful
        assert results["hk2"].reason == "Identity is not set"
        assert challenge == "challenge_obj"
        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_miner_with_duplicate_ip(settings, dummy_miners):
    identities = {
        "hk1": [{"chain": "bittensor", "type": "lite"}],
        "hk2": [{"chain": "bittensor", "type": "archive"}],
        "hk3": [{"chain": "bittensor", "type": "lite"}],
    }
    ip_counts = Counter(m.ip for m in dummy_miners)
    mock_subtensor = AsyncMock()
    executor = ChallengeExecutor(settings, mock_subtensor)

    with patch("subvortex.validator.core.challenger.challenge_executor.execute_challenge") as mock_exec:
        mock_exec.return_value = (
            {
                "hk2": ChallengeResult.create_default(chain="bittensor", type="archive", is_available=True, is_reliable=True),
            },
            "challenge_obj",
        )

        results, challenge = await executor.run(
            step_index=2,
            challengees=dummy_miners,
            identities=identities,
            ip_counts=ip_counts,
        )

        assert not results["hk1"].is_successful
        assert results["hk1"].reason.startswith("2 miners share IP")
        assert not results["hk3"].is_successful
        assert results["hk2"].is_successful
        assert challenge == "challenge_obj"
        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_no_valid_miners(settings, dummy_miners):
    identities = {}
    ip_counts = Counter(m.ip for m in dummy_miners)
    mock_subtensor = AsyncMock()
    executor = ChallengeExecutor(settings, mock_subtensor)

    with patch("subvortex.validator.core.challenger.challenge_executor.execute_challenge") as mock_exec:
        results, challenge = await executor.run(
            step_index=3,
            challengees=dummy_miners,
            identities=identities,
            ip_counts=ip_counts,
        )

        assert all(not r.is_successful for r in results.values())
        assert all(r.reason == "Identity is not set" for r in results.values())
        assert challenge is None
        mock_exec.assert_not_called()
