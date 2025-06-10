import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from collections import Counter

from subvortex.validator.core.challenger.challenger import Challenger
from subvortex.validator.core.challenger.challenge_executor import ChallengeExecutor
from subvortex.validator.core.challenger.challenge_scorer import ChallengeScorer
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.model.miner import Miner
from subvortex.validator.core.challenger.model import ChallengeResult


@pytest.fixture
def dummy_settings():
    s = Settings.create()
    s.logging_name = "test"
    s.netuid = 1
    return s


@pytest.fixture
def dummy_miner():
    return Miner(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")


@pytest.mark.asyncio
async def test_challenger_start_triggers_challenge_flow(dummy_settings, dummy_miner):
    # Simulate increasing block height
    block_counter = [100]

    async def get_block():
        block = block_counter[0]
        block_counter[0] += 1
        return block

    subtensor = AsyncMock()
    subtensor.get_current_block = AsyncMock(side_effect=get_block)

    async def wait_for_block_mock(*args, **kwargs):
            await asyncio.sleep(0.1)
            return True
    
    subtensor.wait_for_block = wait_for_block_mock

    mock_database = AsyncMock()
    mock_database.get_neurons.return_value = []
    mock_database.get_miners.return_value = {"hk1": dummy_miner}
    mock_database.add_schedule = AsyncMock()
    mock_database.add_challenge = AsyncMock()

    executor = AsyncMock(spec=ChallengeExecutor)
    executor.run.return_value = (
        {"hk1": ChallengeResult.create_default("bittensor", "lite")},
        {"challenge_data": "xyz"},
    )

    scorer = AsyncMock(spec=ChallengeScorer)
    scorer.run.return_value = None

    challenger = Challenger(
        hotkey="hk1",
        settings=dummy_settings,
        subtensor=subtensor,
        database=mock_database,
        executor=executor,
        scorer=scorer,
    )

    with patch(
        "subvortex.validator.core.challenger.challenger.extract_countries"
    ) as mock_extract, patch(
        "subvortex.validator.core.challenger.challenger.planner.get_next_cycle"
    ) as mock_cycle, patch(
        "subvortex.validator.core.challenger.challenger.planner.get_schedule"
    ) as mock_schedule, patch(
        "subvortex.validator.core.challenger.challenger.planner.get_next_step"
    ) as mock_step, patch(
        "subvortex.validator.core.challenger.challenger.sci.get_challengee_identities"
    ) as mock_identities, patch(
        "subvortex.validator.core.challenger.challenger.scbs.wait_for_block",
        new_callable=AsyncMock,
    ):

        # Provide mock values for schedule and planner
        mock_extract.return_value = ["US"]
        mock_cycle.return_value = MagicMock(start=100, stop=105)
        mock_schedule.return_value = [
            MagicMock(step_index=0, country="US", id="step-1", block_end=104)
        ]
        mock_step.return_value = (0, 101)
        mock_identities.return_value = {"hk1": [{"chain": "bittensor", "type": "lite"}]}

        # Set timeout to break infinite loop cleanly if something goes wrong
        async def stop_after_start():
            await asyncio.sleep(0.2)
            await challenger.stop()

        # await asyncio.wait_for(
        #     asyncio.gather(challenger.start(), stop_after_start()),
        #     timeout=3,
        # )
        task = asyncio.create_task(challenger.start())
        await asyncio.sleep(0.1)
        await challenger.stop()

        # Await the start task to finish gracefully
        await asyncio.wait_for(task, timeout=1.0)

        # Assert flow ran once
        mock_extract.assert_called_once()
        mock_database.get_neurons.assert_called_once()
        mock_database.get_miners.assert_called_once()
        mock_schedule.assert_called_once()
        mock_identities.assert_called_once()
        executor.run.assert_called_once()
        scorer.run.assert_called_once()
        mock_database.add_challenge.assert_called_once()
