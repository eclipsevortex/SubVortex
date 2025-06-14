import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from subvortex.validator.core.challenger.challenger import Challenger
from subvortex.validator.core.challenger.challenge_executor import ChallengeExecutor
from subvortex.validator.core.challenger.challenge_scorer import ChallengeScorer
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.model.miner import Miner
from subvortex.validator.core.challenger.model import ChallengeResult


@pytest.fixture
def dummy_settings():
    s = Settings.create()
    s.netuid = 1
    return s


@pytest.fixture
def dummy_miner():
    return Miner(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")


@pytest.mark.asyncio
async def test_challenger_start_triggers_challenge_flow(dummy_settings, dummy_miner):
    block_counter = [100]

    async def get_block():
        block = block_counter[0]
        block_counter[0] += 1
        return block

    subtensor = AsyncMock()
    subtensor.get_current_block = AsyncMock(side_effect=get_block)
    subtensor.wait_for_block = AsyncMock()

    # --- Create a gate event to pause the loop inside wait_until_ready ---
    wait_ready_called = asyncio.Event()

    async def wait_until_ready(should_exit, label):
        wait_ready_called.set()
        await asyncio.sleep(1)

    mock_database = AsyncMock()
    mock_database.wait_until_ready = wait_until_ready
    mock_database.get_neuron_last_updated = AsyncMock(return_value=123)
    mock_database.get_neurons = AsyncMock(return_value={"hk1": dummy_miner})
    mock_database.add_schedule = AsyncMock()
    mock_database.add_challenge = AsyncMock()
    mock_database.update_miners = AsyncMock()
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
        "subvortex.validator.core.challenger.challenger.extract_countries",
        return_value=["US"],
    ), patch(
        "subvortex.validator.core.challenger.challenger.planner.get_next_cycle",
        return_value=MagicMock(start=100, stop=105),
    ), patch(
        "subvortex.validator.core.challenger.challenger.planner.get_schedule",
        return_value=[
            MagicMock(step_index=0, country="US", id="step-1", block_end=104)
        ],
    ), patch(
        "subvortex.validator.core.challenger.challenger.planner.get_next_step",
        return_value=(0, 101),
    ), patch(
        "subvortex.validator.core.challenger.challenger.sci.get_challengee_identities",
        return_value={"hk1": [{"chain": "bittensor", "type": "lite"}]},
    ), patch(
        "subvortex.validator.core.challenger.challenger.scss.get_weights_min_stake_async",
        return_value=0,
    ), patch(
        "subvortex.validator.core.challenger.challenger.sync_miners",
        return_value=[dummy_miner],
    ):
        # Run challenger in the background and stop after a short delay
        task = asyncio.create_task(challenger.start())

        # Wait until it's inside wait_until_ready
        await wait_ready_called.wait()

        await challenger.stop()
        await asyncio.wait_for(task, timeout=1.0)

    # Assertions
    mock_database.get_neurons.assert_called_once()
    executor.run.assert_called_once()
    scorer.run.assert_called_once()
    mock_database.add_challenge.assert_called_once()


@pytest.mark.asyncio
async def test_challenger_handles_no_miners_in_step(dummy_settings, dummy_miner):
    # --- Create a gate event to pause the loop inside wait_until_ready ---
    wait_ready_called = asyncio.Event()

    async def wait_until_ready(should_exit, label):
        wait_ready_called.set()
        await asyncio.sleep(1)

    mock_database = AsyncMock()
    mock_database.get_neurons.return_value = {"hk1": dummy_miner}
    mock_database.get_neuron_last_updated.return_value = 123
    mock_database.wait_until_ready = wait_until_ready
    mock_database.add_schedule = AsyncMock()
    mock_database.add_challenge = AsyncMock()

    subtensor = AsyncMock()
    subtensor.get_current_block = AsyncMock(return_value=123)
    executor = AsyncMock(spec=ChallengeExecutor)
    scorer = AsyncMock(spec=ChallengeScorer)

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
    ):

        mock_extract.return_value = ["US"]
        mock_cycle.return_value = MagicMock(start=123, stop=130)
        mock_schedule.return_value = [
            MagicMock(step_index=0, country="US", id="step-1", block_end=130)
        ]
        mock_step.return_value = (0, 124)

        await asyncio.gather(challenger.start(), asyncio.sleep(0.1), challenger.stop())

        executor.run.assert_not_called()
        scorer.run.assert_not_called()
        mock_database.add_challenge.assert_not_called()


@pytest.mark.asyncio
async def test_challenger_skips_sync_if_metagraph_unchanged(dummy_settings):
    # --- Create a gate event to pause the loop inside wait_until_ready ---
    wait_ready_called = asyncio.Event()

    async def wait_until_ready(should_exit, label):
        wait_ready_called.set()
        await asyncio.sleep(1)

    database = AsyncMock()
    database.get_neuron_last_updated.return_value = 50
    database.get_neurons.return_value = {}
    database.wait_until_ready = wait_until_ready

    subtensor = AsyncMock()
    subtensor.get_current_block = AsyncMock(return_value=100)
    subtensor.wait_for_block = AsyncMock()

    executor = AsyncMock()
    scorer = AsyncMock()

    challenger = Challenger(
        hotkey="hk",
        settings=dummy_settings,
        subtensor=subtensor,
        database=database,
        executor=executor,
        scorer=scorer,
    )

    # Force initial and new updates to be the same
    challenger._Challenger__previous_last_update = 50

    with patch(
        "subvortex.validator.core.challenger.challenger.extract_countries",
        return_value=["US"],
    ), patch(
        "subvortex.validator.core.challenger.challenger.planner.get_next_cycle"
    ), patch(
        "subvortex.validator.core.challenger.challenger.planner.get_schedule",
        return_value=[],
    ), patch(
        "subvortex.validator.core.challenger.challenger.planner.get_next_step",
        return_value=(0, 101),
    ):

        await asyncio.gather(challenger.start(), asyncio.sleep(0.1), challenger.stop())

        # Sync and execution logic should not be called
        executor.run.assert_not_called()


@pytest.mark.asyncio
async def test_challenger_waits_for_metagraph_ready(dummy_settings):
    subtensor = AsyncMock()
    subtensor.get_current_block = AsyncMock(return_value=100)
    subtensor.wait_for_block = AsyncMock()

    # Simulate delay in metagraph readiness
    ready_event = asyncio.Event()

    async def wait_until_ready_mock(should_exit, label):
        await ready_event.wait()

    database = AsyncMock()
    database.wait_until_ready = wait_until_ready_mock
    database.get_neuron_last_updated.return_value = 0

    challenger = Challenger(
        hotkey="hk",
        settings=dummy_settings,
        subtensor=subtensor,
        database=database,
        executor=AsyncMock(),
        scorer=AsyncMock(),
    )

    async def trigger_ready():
        await asyncio.sleep(0.1)
        ready_event.set()
        await challenger.stop()

    await asyncio.gather(challenger.start(), trigger_ready())
