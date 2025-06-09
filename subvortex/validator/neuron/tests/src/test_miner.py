import pytest
import numpy as np
from unittest.mock import patch
from unittest.mock import AsyncMock

from subvortex.validator.neuron.src.miner import (
    sync_miners,
    reset_reliability_score,
)
from subvortex.validator.neuron.src.models.miner import Miner
from subvortex.core.model.neuron import Neuron
from subvortex.validator.neuron.src.settings import Settings


def fake_neuron(
    uid: int,
    hotkey: str = "hk",
    ip: str = "1.2.3.4",
    country: str = "US",
    stake: int = 0,
) -> Neuron:
    return Neuron(uid=uid, hotkey=hotkey, ip=ip, country=country, stake=stake)


def fake_miner(
    uid: int,
    hotkey: str = "hk",
    ip: str = "1.2.3.4",
    country: str = "US",
    challenge_attempts: int = 0,
    challenge_successes: int = 0,
) -> Miner:
    miner = Miner.create_new_miner(uid=uid)
    miner.hotkey = hotkey
    miner.ip = ip
    miner.country = country
    miner.challenge_attempts = challenge_attempts
    miner.challenge_successes = challenge_successes
    return miner


@pytest.mark.asyncio
async def test_sync_miners_on_new_miners(monkeypatch):
    db = AsyncMock()
    neuron = fake_neuron(1)
    neurons = {f"hk1": neuron}
    miners = []
    moving_scores = np.where(np.arange(256) == neuron.uid, 0, 1)
    validator = fake_neuron(999, country="US")

    logs = []

    def mock_log(msg):
        logs.append(msg)

    monkeypatch.setattr("bittensor.utils.btlogging.logging.info", mock_log)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )

    assert any("New miner discovered" in log for log in logs)
    assert len(result_miners) == 1
    db.remove_miner.assert_not_called()
    assert result_miners[0].uid == neuron.uid
    assert result_miners[0].rank == -1
    assert result_miners[0].ip == neuron.ip
    assert result_miners[0].port == neuron.port
    assert result_miners[0].coldkey == neuron.coldkey
    assert result_miners[0].hotkey == neuron.hotkey
    assert result_miners[0].country == neuron.country
    assert result_miners[0].version == "0.0.0"
    assert result_miners[0].score == 0
    assert result_miners[0].availability_score == 0
    assert result_miners[0].reliability_score == 0
    assert result_miners[0].latency_score == 0
    assert result_miners[0].distribution_score == 0
    assert result_miners[0].challenge_successes == 0
    assert result_miners[0].challenge_attempts == 0
    assert result_miners[0].process_time == 0
    assert result_miners[0].verified == False
    assert result_miners[0].sync == False
    assert result_miners[0].suspicious == False
    assert result_miners[0].penalty_factor == None
    assert result_scores[neuron.uid] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i != neuron.uid)


@pytest.mark.asyncio
async def test_sync_miners_multiple_new_miners(monkeypatch):
    db = AsyncMock()
    neurons = {
        "hk1": fake_neuron(1, hotkey="hk1", ip="1.1.1.1"),
        "hk2": fake_neuron(2, hotkey="hk2", ip="2.2.2.2"),
    }
    miners = []
    validator = fake_neuron(999, country="US")
    moving_scores = np.ones(256)

    logs = []

    def mock_log(msg):
        logs.append(msg)

    monkeypatch.setattr("bittensor.utils.btlogging.logging.info", mock_log)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )

    assert any("New miner discovered" in log for log in logs)
    assert len(result_miners) == 2
    db.remove_miner.assert_not_called()
    for i in range(2):
        hotkey = result_miners[i].hotkey
        assert result_miners[i].uid == neurons[hotkey].uid
        assert result_miners[i].rank == -1
        assert result_miners[i].ip == neurons[hotkey].ip
        assert result_miners[i].port == neurons[hotkey].port
        assert result_miners[i].coldkey == neurons[hotkey].coldkey
        assert result_miners[i].hotkey == neurons[hotkey].hotkey
        assert result_miners[i].country == neurons[hotkey].country
        assert result_miners[i].version == "0.0.0"
        assert result_miners[i].score == 0
        assert result_miners[i].availability_score == 0
        assert result_miners[i].reliability_score == 0
        assert result_miners[i].latency_score == 0
        assert result_miners[i].distribution_score == 0
        assert result_miners[i].challenge_successes == 0
        assert result_miners[i].challenge_attempts == 0
        assert result_miners[i].process_time == 0
        assert result_miners[i].verified == False
        assert result_miners[i].sync == False
        assert result_miners[i].suspicious == False
        assert result_miners[i].penalty_factor == None

    assert result_scores[1] == 0
    assert result_scores[2] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i not in [1, 2])


@pytest.mark.asyncio
async def test_sync_miners_on_hotkey_change(monkeypatch):
    db = AsyncMock()
    neuron = fake_neuron(1, hotkey="new_hk")
    neurons = {"new_hk": neuron}
    miner = fake_miner(1, hotkey="old_hk")
    miner.rank = 1
    miner.version = "3.1.1"
    miner.verified = True
    miner.sync = True
    miner.suspicious = False
    miner.penalty_factor = None
    miner.score = 0.83
    miner.availability_score = 0.45
    miner.reliability_score = 0.65
    miner.latency_score = 0.47
    miner.distribution_score = 0.46
    miner.challenge_successes = 10
    miner.challenge_attempts = 11
    miner.process_time = 0.50
    miners = [miner]
    validator = fake_neuron(999, country="US")
    moving_scores = np.ones(256)

    logs = []

    def mock_log(msg):
        logs.append(msg)

    monkeypatch.setattr("bittensor.utils.btlogging.logging.info", mock_log)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )

    assert any("Hotkey change detected" in log for log in logs)
    db.remove_miner.assert_called_once_with(miner=miner)
    assert result_miners[0].rank == -1
    assert result_miners[0].version == "0.0.0"
    assert result_miners[0].verified == False
    assert result_miners[0].sync == False
    assert result_miners[0].suspicious == False
    assert result_miners[0].penalty_factor == None
    assert result_miners[0].score == 0
    assert result_miners[0].availability_score == 0
    assert result_miners[0].reliability_score == 0
    assert result_miners[0].latency_score == 0
    assert result_miners[0].distribution_score == 0
    assert result_miners[0].challenge_successes == 0
    assert result_miners[0].challenge_attempts == 0
    assert result_miners[0].process_time == 0
    assert result_scores[1] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i != 1)


@pytest.mark.asyncio
async def test_sync_miners_on_ip_change_with_same_country(monkeypatch):
    db = AsyncMock()
    neuron = fake_neuron(1, ip="5.5.5.5", country="US")
    neurons = {neuron.hotkey: neuron}
    miner = fake_miner(1, ip="1.1.1.1", country="US")
    miner.rank = 1
    miner.version = "3.1.1"
    miner.verified = True
    miner.sync = True
    miner.suspicious = False
    miner.penalty_factor = None
    miner.score = 0.83
    miner.availability_score = 0.45
    miner.reliability_score = 0.65
    miner.latency_score = 0.47
    miner.distribution_score = 0.46
    miner.challenge_successes = 10
    miner.challenge_attempts = 11
    miner.process_time = 0.50
    miners = [miner]
    validator = fake_neuron(999, country="US")
    moving_scores = np.ones(256)

    logs = []

    def mock_log(msg):
        logs.append(msg)

    monkeypatch.setattr("bittensor.utils.btlogging.logging.info", mock_log)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )

    assert any("IP change detected" in log for log in logs)
    db.remove_miner.assert_not_called()
    assert result_miners[0].uid == neuron.uid
    assert result_miners[0].rank == -1
    assert result_miners[0].ip == neuron.ip
    assert result_miners[0].hotkey == neuron.hotkey
    assert result_miners[0].country == neuron.country
    assert result_miners[0].version == "0.0.0"
    assert result_miners[0].verified == False
    assert result_miners[0].sync == False
    assert result_miners[0].suspicious == False
    assert result_miners[0].penalty_factor == None
    assert result_miners[0].score == 0
    assert result_miners[0].availability_score == 0
    assert result_miners[0].reliability_score == 0
    assert result_miners[0].latency_score == 0
    assert result_miners[0].distribution_score == 0
    assert result_miners[0].challenge_successes == 0
    assert result_miners[0].challenge_attempts == 0
    assert result_miners[0].process_time == 0
    assert all(result_scores[i] == 1 for i in range(256))


@pytest.mark.asyncio
async def test_sync_miners_on_ip_and_country_change(monkeypatch):
    db = AsyncMock()
    neuron = fake_neuron(1, ip="5.5.5.5", country="CA")
    neurons = {neuron.hotkey: neuron}
    miner = fake_miner(1, ip="1.1.1.1", country="US")
    miner.rank = 1
    miner.version = "3.1.1"
    miner.verified = True
    miner.sync = True
    miner.suspicious = False
    miner.penalty_factor = None
    miner.score = 0.83
    miner.availability_score = 0.45
    miner.reliability_score = 0.65
    miner.latency_score = 0.47
    miner.distribution_score = 0.46
    miner.challenge_successes = 10
    miner.challenge_attempts = 11
    miner.process_time = 0.50
    miners = [miner]
    validator = fake_neuron(999, country="US")
    moving_scores = np.ones(256)

    logs = []

    def mock_log(msg):
        logs.append(msg)

    monkeypatch.setattr("bittensor.utils.btlogging.logging.info", mock_log)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )

    assert any("IP change detected" in log for log in logs)
    db.remove_miner.assert_not_called()
    assert result_miners[0].uid == neuron.uid
    assert result_miners[0].rank == -1
    assert result_miners[0].ip == neuron.ip
    assert result_miners[0].hotkey == neuron.hotkey
    assert result_miners[0].country == neuron.country
    assert result_miners[0].version == "0.0.0"
    assert result_miners[0].verified == False
    assert result_miners[0].sync == False
    assert result_miners[0].suspicious == False
    assert result_miners[0].penalty_factor == None
    assert result_miners[0].score == 0
    assert result_miners[0].availability_score == 0
    assert result_miners[0].reliability_score == 0
    assert result_miners[0].latency_score == 0
    assert result_miners[0].distribution_score == 0
    assert result_miners[0].challenge_successes == 0
    assert result_miners[0].challenge_attempts == 0
    assert result_miners[0].process_time == 0
    assert result_scores[1] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i != 1)


@pytest.mark.asyncio
async def test_sync_miners_skips_unchanged_miners():
    db = AsyncMock()
    neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")
    miner = fake_miner(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")
    miner.rank = 1
    miner.version = "3.1.1"
    miner.verified = True
    miner.sync = True
    miner.suspicious = False
    miner.penalty_factor = None
    miner.score = 0.9475
    miner.availability_score = 1
    miner.reliability_score = 0.65
    miner.latency_score = 1
    miner.distribution_score = 1
    miner.challenge_successes = 10
    miner.challenge_attempts = 11
    miner.process_time = 0.50
    miners = [miner]
    moving_scores = np.ones(256)
    validator = fake_neuron(uid=999, country="US")

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        {"hk1": neuron},
        miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )

    assert len(result_miners) == 1
    db.remove_miner.assert_not_called()
    assert result_miners[0].uid == neuron.uid
    assert result_miners[0].rank == 1
    assert result_miners[0].ip == neuron.ip
    assert result_miners[0].hotkey == neuron.hotkey
    assert result_miners[0].country == neuron.country
    assert result_miners[0].version == miner.version
    assert result_miners[0].score == miner.score
    assert result_miners[0].availability_score == miner.availability_score
    assert result_miners[0].reliability_score == miner.reliability_score
    assert result_miners[0].latency_score == miner.latency_score
    assert result_miners[0].distribution_score == miner.distribution_score
    assert result_miners[0].challenge_successes == miner.challenge_successes
    assert result_miners[0].challenge_attempts == miner.challenge_attempts
    assert result_miners[0].process_time == miner.process_time
    assert result_miners[0].verified == miner.verified
    assert result_miners[0].sync == miner.sync
    assert result_miners[0].suspicious == miner.suspicious
    assert result_miners[0].penalty_factor == miner.penalty_factor
    assert all(result_scores[i] == 1 for i in range(256))


@pytest.mark.asyncio
async def test_sync_miners_removes_stale_miners():
    db = AsyncMock()
    neuron = fake_neuron(uid=1, hotkey="hk1")
    neurons = {"hk1": neuron}
    miners = [fake_miner(uid=1, hotkey="hk1"), fake_miner(uid=2, hotkey="hk2")]  # stale
    validator = fake_neuron(uid=999, country="US")
    moving_scores = np.ones(256)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )

    db.remove_miner.assert_called_once()
    assert db.remove_miner.call_args[1]["miner"].uid == 2
    assert result_miners[0].uid == 1
    assert result_scores[2] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i != 2)


@pytest.mark.asyncio
async def test_sync_miners_removes_multiple_stale_miners():
    db = AsyncMock()
    neurons = {"hk10": fake_neuron(uid=10, hotkey="hk10")}
    stale_miners = [
        fake_miner(uid=1, hotkey="hk1"),
        fake_miner(uid=2, hotkey="hk2"),
        fake_miner(uid=3, hotkey="hk3"),
        fake_miner(uid=10, hotkey="hk10"),
    ]
    validator = fake_neuron(uid=999, country="US")
    moving_scores = np.ones(256)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        stale_miners,
        validator,
        min_stake=1000,
        moving_scores=moving_scores,
    )
    assert db.remove_miner.call_count == 3
    removed_uids = {call.kwargs["miner"].uid for call in db.remove_miner.call_args_list}
    assert removed_uids == {1, 2, 3}
    assert len(result_miners) == 1
    assert result_miners[0].uid == 10

    assert result_scores[1] == 0
    assert result_scores[2] == 0
    assert result_scores[3] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i not in [1, 2, 3])


@pytest.mark.asyncio
async def test_sync_miners_does_not_remove_valid_miners():
    db = AsyncMock()
    neurons = {"hk1": fake_neuron(uid=1, hotkey="hk1")}
    miners = [fake_miner(uid=1, hotkey="hk1")]
    validator = fake_neuron(uid=999, country="US")

    result, _ = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=1000,
        moving_scores=np.ones(256),
    )

    db.remove_miner.assert_not_called()
    assert len(result) == 1
    assert result[0].uid == 1


@pytest.mark.asyncio
async def test_sync_miners_skips_neuron_above_min_stake():
    db = AsyncMock()

    neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.1.1.1", country="US")
    neuron.stake = 500
    neuron.validator_trust = 0

    neurons = {"hk1": neuron}
    miners = [fake_miner(uid=1, hotkey="hk1", ip="1.1.1.1", country="US")]
    validator = fake_neuron(uid=999, country="US")
    validator.stake = 1000
    moving_scores = np.ones(256)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=100,
        moving_scores=moving_scores,
    )

    assert result_miners == []
    assert result_scores[1] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i != 1)


@pytest.mark.asyncio
async def test_sync_miners_skips_neuron_with_validator_trust():
    db = AsyncMock()

    neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.1.1.1", country="US")
    neuron.stake = 10
    neuron.validator_trust = 0.1

    neurons = {"hk1": neuron}
    miners = [fake_miner(uid=1, hotkey="hk1", ip="1.1.1.1", country="US")]
    validator = fake_neuron(uid=999, country="US")
    validator.stake = 1000
    moving_scores = np.ones(256)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=100,
        moving_scores=moving_scores,
    )

    assert result_miners == []
    assert result_scores[1] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i != 1)


@pytest.mark.asyncio
async def test_sync_miners_skips_neuron_being_the_current_validator():
    db = AsyncMock()

    neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.1.1.1", country="US")
    neuron.stake = 0
    neuron.validator_trust = 0
    neurons = {"hk1": neuron}
    miners = [fake_miner(uid=1, hotkey="hk1", ip="1.1.1.1", country="US")]
    moving_scores = np.ones(256)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        neuron,
        min_stake=100,
        moving_scores=moving_scores,
    )

    assert result_miners == []
    assert result_scores[1] == 0
    assert all(result_scores[i] == 1 for i in range(256) if i != 1)


@pytest.mark.asyncio
async def test_sync_miners_includes_neuron_not_considered_a_validator():
    db = AsyncMock()

    neuron = fake_neuron(uid=2, hotkey="hk2", ip="2.2.2.2", country="US")
    neuron.stake = 10
    neuron.validator_trust = 0

    neurons = {"hk2": neuron}
    miners = [fake_miner(uid=2, hotkey="hk2", ip="2.2.2.2", country="US")]
    validator = fake_neuron(uid=999, country="US")
    validator.stake = 1000
    moving_scores = np.ones(256)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons,
        miners,
        validator,
        min_stake=100,
        moving_scores=moving_scores,
    )

    assert len(result_miners) == 1
    assert result_miners[0].uid == neuron.uid
    assert all(result_scores[i] == 1 for i in range(256))


@pytest.mark.asyncio
async def test_sync_miners_empty_inputs():
    db = AsyncMock()
    moving_scores = np.ones(256)

    result_miners, result_scores = await sync_miners(
        Settings(),
        db,
        neurons={},
        miners=[],
        validator=fake_neuron(999),
        min_stake=1000,
        moving_scores=moving_scores,
    )

    assert result_miners == []
    db.remove_miner.assert_not_called()
    assert all(result_scores[i] == 1 for i in range(256))


@pytest.mark.asyncio
async def test_sync_miners_respects_is_test_flag():
    # Arrange
    db = AsyncMock()
    validator = fake_neuron(999, country="US")
    high_stake_miner = fake_neuron(uid=1, hotkey="hk1", stake=10_000)
    settings = Settings()
    settings.netuid = 92
    neurons = {"hk1": high_stake_miner}
    miners = []
    locations = ["US"]

    # Act
    result, _ = await sync_miners(
        settings,
        db,
        neurons,
        miners,
        validator,
        min_stake=100_000,
        moving_scores=np.ones(256),
    )

    # Assert
    assert len(result) == 1


@pytest.mark.asyncio
async def test_reset_reliability_score_sets_zero():
    db = AsyncMock()
    miner1 = fake_miner(1, challenge_attempts=5, challenge_successes=3)
    miner2 = fake_miner(2, challenge_attempts=7, challenge_successes=2)

    miners = [miner1, miner2]

    await reset_reliability_score(db, miners)

    for miner in miners:
        assert miner.challenge_attempts == 0
        assert miner.challenge_successes == 0

    db.update_miners.assert_called_once_with(miners=miners)


@pytest.mark.asyncio
async def test_reset_reliability_score_empty_list():
    db = AsyncMock()
    miners = []

    await reset_reliability_score(db, miners)
    db.update_miners.assert_called_once_with(miners=[])
