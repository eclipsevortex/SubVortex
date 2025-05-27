import pytest
from unittest.mock import AsyncMock

from subvortex.validator.neuron.src.miner import get_miners, sync_miners, reset_reliability_score
from subvortex.validator.neuron.src.models.miner import Miner
from subvortex.core.model.neuron import Neuron


def fake_neuron(uid: int, hotkey: str = "hk", ip: str = "1.2.3.4", country: str = "US") -> Neuron:
    return Neuron(uid=uid, hotkey=hotkey, ip=ip, country=country)


def fake_miner(uid: int, hotkey: str = "hk", ip: str = "1.2.3.4", country: str = "US") -> Miner:
    miner = Miner.create_new_miner(uid=uid)
    miner.hotkey = hotkey
    miner.ip = ip
    miner.country = country
    return miner


@pytest.mark.asyncio
async def test_get_miners_creates_new_miners():
    db = AsyncMock()
    neuron = fake_neuron(1)
    db.get_neurons.return_value = {neuron.hotkey: neuron}
    db.get_miner.return_value = None

    miners = await get_miners(db)

    assert len(miners) == 1
    assert miners[0].uid == neuron.uid
    db.add_miner.assert_called_once()


@pytest.mark.asyncio
async def test_get_miners_returns_existing_miners():
    db = AsyncMock()
    neuron = fake_neuron(1)
    miner = fake_miner(1)
    db.get_neurons.return_value = {neuron.hotkey: neuron}
    db.get_miner.return_value = miner

    miners = await get_miners(db)

    assert miners == [miner]
    db.add_miner.assert_not_called()


@pytest.mark.asyncio
async def test_sync_miners_adds_missing_miners():
    db = AsyncMock()
    neurons = {f"hk1": fake_neuron(1)}
    miners = []
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    result = await sync_miners(db, neurons, miners, validator, locations)

    assert len(result) == 1
    assert result[0].uid == 1
    # db.add_miner.assert_called_once()


@pytest.mark.asyncio
async def test_sync_miners_handles_hotkey_change():
    db = AsyncMock()
    neurons = {"new_hk": fake_neuron(1, hotkey="new_hk")}
    current = fake_miner(1, hotkey="old_hk")
    miners = [current]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    await sync_miners(db, neurons, miners, validator, locations)

    db.remove_miner.assert_called_once()


@pytest.mark.asyncio
async def test_sync_miners_detects_ip_change_logs(monkeypatch):
    db = AsyncMock()
    neurons = {"hk1": fake_neuron(1, ip="1.1.1.1")}
    miner = fake_miner(1, ip="8.8.8.8")
    miners = [miner]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    logs = []

    def mock_success(msg):
        logs.append(msg)

    monkeypatch.setattr("bittensor.utils.btlogging.logging.success", mock_success)

    await sync_miners(db, neurons, miners, validator, locations)

    assert any("Miner moved from" in log for log in logs)


@pytest.mark.asyncio
async def test_reset_reliability_score_sets_zero():
    db = AsyncMock()
    miner1 = fake_miner(1)
    miner1.challenge_attempts = 5
    miner1.challenge_successes = 3

    miner2 = fake_miner(2)
    miner2.challenge_attempts = 7
    miner2.challenge_successes = 2

    miners = [miner1, miner2]

    await reset_reliability_score(db, miners)

    for miner in miners:
        assert miner.challenge_attempts == 0
        assert miner.challenge_successes == 0

    db.update_miners.assert_called_once_with(miners=miners)


@pytest.mark.asyncio
async def test_sync_miners_updates_visible_outside():
    db = AsyncMock()
    
    # Initial data: one neuron in DB, one existing miner
    neuron = fake_neuron(uid=1, ip="10.0.0.1", hotkey="hk1")
    db_neurons = {"hk1": neuron}

    # Existing miner with different IP (will be updated)
    miner = fake_miner(uid=1, ip="192.168.1.1", hotkey="hk1")
    miners = [miner]

    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    result = await sync_miners(db, db_neurons, miners, validator, locations)

    # Assert that the original miner object has been mutated
    assert result[0].ip == "10.0.0.1"
    assert result[0].hotkey == "hk1"
    assert result[0].uid == 1