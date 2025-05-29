import pytest
from unittest.mock import patch
from unittest.mock import AsyncMock

from subvortex.validator.neuron.src.miner import (
    get_miners,
    sync_miners,
    reset_reliability_score,
)
from subvortex.validator.neuron.src.models.miner import Miner
from subvortex.core.model.neuron import Neuron


def fake_neuron(
    uid: int, hotkey: str = "hk", ip: str = "1.2.3.4", country: str = "US"
) -> Neuron:
    return Neuron(uid=uid, hotkey=hotkey, ip=ip, country=country)


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
async def test_get_miners_creates_new_miners():
    db = AsyncMock()
    neuron = fake_neuron(1)
    db.get_neurons.return_value = {neuron.hotkey: neuron}
    db.get_miner.return_value = None

    miners = await get_miners(db)

    assert len(miners) == 1
    assert miners[0].uid == neuron.uid
    assert miners[0].ip == neuron.ip
    assert miners[0].hotkey == neuron.hotkey
    assert miners[0].country == neuron.country
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
    assert miners[0] == miner
    db.add_miner.assert_not_called()


@pytest.mark.asyncio
async def test_sync_miners_handle_new_miners():
    db = AsyncMock()
    neuron = fake_neuron(1)
    neurons = {f"hk1": neuron}
    miners = []
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    result = await sync_miners(db, neurons, miners, validator, locations)

    assert len(result) == 1
    assert result[0].uid == neuron.uid
    assert result[0].ip == neuron.ip
    assert result[0].hotkey == neuron.hotkey
    assert result[0].country == neuron.country
    assert result[0].version == "0.0.0"
    assert result[0].score == 0
    assert result[0].availability_score == 0
    assert result[0].reliability_score == 0
    assert result[0].latency_score == 0
    assert result[0].distribution_score == 0
    assert result[0].challenge_successes == 0
    assert result[0].challenge_attempts == 0
    assert result[0].process_time == 0
    assert result[0].verified == False
    assert result[0].sync == False
    assert result[0].suspicious == False
    assert result[0].penalty_factor == None


@pytest.mark.asyncio
async def test_sync_miners_handle_hotkey_change():
    db = AsyncMock()
    neurons = {"new_hk": fake_neuron(1, hotkey="new_hk")}
    current = fake_miner(1, hotkey="old_hk")
    current.version = "3.1.1"
    current.verified = True
    current.sync = True
    current.suspicious = False
    current.penalty_factor = None
    current.score = 0.83
    current.availability_score = 0.45
    current.reliability_score = 0.65
    current.latency_score = 0.47
    current.distribution_score = 0.46
    current.challenge_successes = 0.48
    current.challenge_attempts = 0.49
    current.process_time = 0.50
    miners = [current]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    result = await sync_miners(db, neurons, miners, validator, locations)

    db.remove_miner.assert_called_once()
    assert result[0].version == "0.0.0"
    assert result[0].verified == False
    assert result[0].sync == False
    assert result[0].suspicious == False
    assert result[0].penalty_factor == None
    assert result[0].score == 0
    assert result[0].availability_score == 0
    assert result[0].reliability_score == 0
    assert result[0].latency_score == 0
    assert result[0].distribution_score == 0
    assert result[0].challenge_successes == 0
    assert result[0].challenge_attempts == 0
    assert result[0].process_time == 0


@pytest.mark.asyncio
async def test_sync_miners_handle_ip_change(monkeypatch):
    db = AsyncMock()
    neuron = fake_neuron(1, ip="1.1.1.1")
    neurons = {"hk1": neuron}
    miner = fake_miner(1, hotkey="old_hk")
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
    miner.challenge_successes = 0.48
    miner.challenge_attempts = 0.49
    miner.process_time = 0.50
    miners = [miner]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    logs = []

    def mock_log(msg):
        logs.append(msg)

    monkeypatch.setattr("bittensor.utils.btlogging.logging.info", mock_log)

    result = await sync_miners(db, neurons, miners, validator, locations)

    assert any("IP address changed from" in log for log in logs)
    assert result[0].uid == neuron.uid
    assert result[0].ip == neuron.ip
    assert result[0].hotkey == neuron.hotkey
    assert result[0].country == neuron.country
    assert result[0].version == "0.0.0"
    assert result[0].verified == False
    assert result[0].sync == False
    assert result[0].suspicious == False
    assert result[0].penalty_factor == None
    assert result[0].score == 0
    assert result[0].availability_score == 0
    assert result[0].reliability_score == 0
    assert result[0].latency_score == 0
    assert result[0].distribution_score == 0
    assert result[0].challenge_successes == 0
    assert result[0].challenge_attempts == 0
    assert result[0].process_time == 0


@pytest.mark.asyncio
async def test_sync_miners_skips_unchanged_miners():
    db = AsyncMock()
    neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")
    miner = fake_miner(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")
    miners = [miner]
    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    result = await sync_miners(db, {"hk1": neuron}, miners, validator, locations)

    assert len(result) == 1
    db.remove_miner.assert_not_called()
    assert result[0].uid == neuron.uid
    assert result[0].ip == neuron.ip
    assert result[0].hotkey == neuron.hotkey
    assert result[0].country == neuron.country
    assert result[0].version == "0.0.0"
    assert result[0].score == 0
    assert result[0].availability_score == 0
    assert result[0].reliability_score == 0
    assert result[0].latency_score == 0
    assert result[0].distribution_score == 0
    assert result[0].challenge_successes == 0
    assert result[0].challenge_attempts == 0
    assert result[0].process_time == 0
    assert result[0].verified == False
    assert result[0].sync == False
    assert result[0].suspicious == False
    assert result[0].penalty_factor == None


@pytest.mark.asyncio
async def test_sync_miners_all_scores_are_recalculated():
    db = AsyncMock()
    neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")
    miner = fake_miner(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")

    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    with patch(
        "subvortex.validator.neuron.src.miner.compute_availability_score",
        return_value=0.11,
    ), patch(
        "subvortex.validator.neuron.src.miner.compute_latency_score", return_value=0.22
    ), patch(
        "subvortex.validator.neuron.src.miner.compute_distribution_score",
        return_value=0.33,
    ), patch(
        "subvortex.validator.neuron.src.miner.compute_final_score", return_value=0.44
    ):

        result = await sync_miners(db, {"hk1": neuron}, [miner], validator, locations)
        updated_miner = result[0]

        assert updated_miner.availability_score == 0.11
        assert updated_miner.latency_score == 0.22
        assert updated_miner.distribution_score == 0.33
        assert updated_miner.score == 0.44


@pytest.mark.asyncio
async def test_sync_miners_ip_conflict_affects_all_scores():
    db = AsyncMock()

    shared_ip = "1.1.1.1"
    neuron1 = fake_neuron(uid=1, hotkey="hk1", ip=shared_ip)
    neuron2 = fake_neuron(uid=2, hotkey="hk2", ip=shared_ip)

    miner1 = fake_miner(uid=1, hotkey="hk1", ip=shared_ip)
    miner2 = fake_miner(uid=2, hotkey="hk2", ip=shared_ip)

    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    with patch(
        "subvortex.validator.neuron.src.miner.compute_availability_score",
        side_effect=[0.11, 0.11],
    ) as mock_avail, patch(
        "subvortex.validator.neuron.src.miner.compute_latency_score",
        side_effect=[0.22, 0.22],
    ) as mock_latency, patch(
        "subvortex.validator.neuron.src.miner.compute_distribution_score",
        side_effect=[0.33, 0.33],
    ) as mock_dist, patch(
        "subvortex.validator.neuron.src.miner.compute_final_score",
        side_effect=[0.44, 0.44],
    ) as mock_final:

        result = await sync_miners(
            db,
            {"hk1": neuron1, "hk2": neuron2},
            [miner1, miner2],
            validator,
            locations,
        )

        assert result[0].ip == result[1].ip == shared_ip

        # Check each score explicitly
        assert result[0].availability_score == 0.11
        assert result[1].availability_score == 0.11

        assert result[0].latency_score == 0.22
        assert result[1].latency_score == 0.22

        assert result[0].distribution_score == 0.33
        assert result[1].distribution_score == 0.33

        assert result[0].score == 0.44
        assert result[1].score == 0.44

        # Ensure the scoring functions were called with conflict
        mock_avail.assert_called()
        mock_latency.assert_called()
        mock_dist.assert_called()
        mock_final.assert_called()


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
