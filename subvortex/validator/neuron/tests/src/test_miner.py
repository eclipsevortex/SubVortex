import pytest
from unittest.mock import patch
from unittest.mock import AsyncMock

from subvortex.validator.neuron.src.miner import (
    sync_miners,
    reset_reliability_score,
)
from subvortex.validator.neuron.src.models.miner import Miner
from subvortex.core.model.neuron import Neuron


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
async def test_sync_miners_handle_new_miners():
    db = AsyncMock()
    neuron = fake_neuron(1)
    neurons = {f"hk1": neuron}
    miners = []
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

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

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

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
    neurons = {neuron.hotkey: neuron}
    miner = fake_miner(1)
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

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

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
async def test_sync_miners_resets_on_hotkey_and_ip_change():
    db = AsyncMock()
    neurons = {"new_hk": fake_neuron(1, hotkey="new_hk", ip="2.2.2.2")}
    current = fake_miner(1, hotkey="old_hk", ip="1.1.1.1")

    miners = [current]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    db.remove_miner.assert_called_once()
    assert result[0].hotkey == "new_hk"
    assert result[0].ip == "2.2.2.2"


@pytest.mark.asyncio
async def test_sync_miners_skips_unchanged_miners():
    db = AsyncMock()
    neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")
    miner = fake_miner(uid=1, hotkey="hk1", ip="1.2.3.4", country="US")
    miners = [miner]
    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, {"hk1": neuron}, miners, validator, locations, min_stake=1000
    )

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
async def test_sync_miners_ip_conflict_affects_all_scores():
    db = AsyncMock()

    neuron1 = fake_neuron(uid=1, hotkey="hk1", ip="1.1.1.1")
    neuron2 = fake_neuron(uid=2, hotkey="hk2", ip="1.1.1.2")

    miner1 = fake_miner(uid=1, hotkey="hk1", ip="1.1.1.3")
    miner2 = fake_miner(uid=2, hotkey="hk2", ip="1.1.1.4")

    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    with (
        patch(
            "subvortex.validator.neuron.src.miner.compute_availability_score",
            side_effect=[0.11, 0.11],
        ) as mock_avail,
        patch(
            "subvortex.validator.neuron.src.miner.compute_latency_score",
            side_effect=[0.22, 0.22],
        ) as mock_latency,
        patch(
            "subvortex.validator.neuron.src.miner.compute_distribution_score",
            side_effect=[0.33, 0.33],
        ) as mock_dist,
        patch(
            "subvortex.validator.neuron.src.miner.compute_final_score",
            side_effect=[0.44, 0.44],
        ) as mock_final,
    ):

        result, reset_miners = await sync_miners(
            db,
            {"hk1": neuron1, "hk2": neuron2},
            [miner1, miner2],
            validator,
            locations,
            min_stake=1000,
        )

        assert result[0].ip == "1.1.1.1"
        assert result[1].ip == "1.1.1.2"

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


@pytest.mark.asyncio
async def test_sync_miners_removes_stale_miners():
    db = AsyncMock()
    neurons = {"hk1": fake_neuron(uid=1, hotkey="hk1")}
    miners = [fake_miner(uid=2, hotkey="hk2")]  # stale
    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    db.remove_miner.assert_called_once()
    assert db.remove_miner.call_args[1]["miner"].uid == 2
    assert result[0].uid == 1


@pytest.mark.asyncio
async def test_sync_miners_does_not_remove_valid_miners():
    db = AsyncMock()
    neurons = {"hk1": fake_neuron(uid=1, hotkey="hk1")}
    miners = [fake_miner(uid=1, hotkey="hk1")]
    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    db.remove_miner.assert_not_called()
    assert len(result) == 1
    assert result[0].uid == 1


@pytest.mark.asyncio
async def test_sync_miners_removes_multiple_stale_miners():
    db = AsyncMock()
    neurons = {"hk10": fake_neuron(uid=10, hotkey="hk10")}
    stale_miners = [
        fake_miner(uid=1, hotkey="hk1"),
        fake_miner(uid=2, hotkey="hk2"),
        fake_miner(uid=3, hotkey="hk3"),
    ]
    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, stale_miners, validator, locations, min_stake=1000
    )
    assert db.remove_miner.call_count == 3
    removed_uids = {call.kwargs["miner"].uid for call in db.remove_miner.call_args_list}
    assert removed_uids == {1, 2, 3}
    assert len(result) == 1
    assert result[0].uid == 10


@pytest.mark.asyncio
async def test_sync_miners_skips_miners_above_min_stake():
    db = AsyncMock()

    low_stake_neuron = fake_neuron(uid=1, hotkey="hk1", ip="1.1.1.1", country="US")
    low_stake_neuron.stake = 500

    neurons = {"hk1": low_stake_neuron}
    miners = []
    validator = fake_neuron(uid=999, country="US")
    validator.stake = 1000
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=100
    )

    assert result == []  # Should skip due to low stake
    db.remove_miner.assert_not_called()


@pytest.mark.asyncio
async def test_sync_miners_includes_miners_below_min_stake():
    db = AsyncMock()

    high_stake_neuron = fake_neuron(uid=2, hotkey="hk2", ip="2.2.2.2", country="US")
    high_stake_neuron.stake = 10

    neurons = {"hk2": high_stake_neuron}
    miners = []
    validator = fake_neuron(uid=999, country="US")
    validator.stake = 1000
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=100
    )

    assert len(result) == 1
    assert result[0].uid == high_stake_neuron.uid


@pytest.mark.asyncio
async def test_sync_miners_skips_validator_even_if_stake_below_min():
    db = AsyncMock()

    validator = fake_neuron(uid=42, hotkey="hk42", country="US")
    validator.stake = 0  # Even if below min_stake
    validator.validator_trust = 1.0  # Treated as validator

    neurons = {"hk42": validator}
    miners = []
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=100
    )

    assert result == []


@pytest.mark.asyncio
async def test_sync_miners_empty_inputs():
    db = AsyncMock()
    result, reset_miners = await sync_miners(
        db,
        neurons={},
        miners=[],
        validator=fake_neuron(999),
        locations=[],
        min_stake=1000,
    )
    assert result == []
    db.remove_miner.assert_not_called()


@pytest.mark.asyncio
async def test_reset_reliability_score_empty_list():
    db = AsyncMock()
    miners = []

    await reset_reliability_score(db, miners)
    db.update_miners.assert_called_once_with(miners=[])


@pytest.mark.asyncio
async def test_sync_miners_multiple_new_miners():
    db = AsyncMock()
    neurons = {
        "hk1": fake_neuron(1, hotkey="hk1", ip="1.1.1.1"),
        "hk2": fake_neuron(2, hotkey="hk2", ip="2.2.2.2"),
    }
    miners = []
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )
    assert len(result) == 2
    assert set([m.uid for m in result]) == {1, 2}


@pytest.mark.asyncio
async def test_sync_miners_removes_and_readds_stale_miner():
    db = AsyncMock()
    old_miner = fake_miner(uid=1, hotkey="old_hk", ip="1.1.1.1")
    neurons = {"new_hk": fake_neuron(uid=1, hotkey="new_hk", ip="2.2.2.2")}
    validator = fake_neuron(uid=999, country="US")
    locations = ["US", "CA"]

    result, reset_miners = await sync_miners(
        db, neurons, [old_miner], validator, locations, min_stake=1000
    )

    db.remove_miner.assert_called_once()
    assert result[0].hotkey == "new_hk"
    assert result[0].ip == "2.2.2.2"


@pytest.mark.asyncio
async def test_sync_miners_returns_reset_miners_on_hotkey_change():
    db = AsyncMock()
    neurons = {"new_hk": fake_neuron(1, hotkey="new_hk")}
    current = fake_miner(1, hotkey="old_hk")
    miners = [current]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    updated_miners, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    assert len(updated_miners) == 1
    assert len(reset_miners) == 1
    assert reset_miners[0].uid == 1
    assert reset_miners[0].hotkey == "old_hk"


@pytest.mark.asyncio
async def test_sync_miners_returns_reset_miners_on_ip_change_and_same_country():
    db = AsyncMock()
    neuron = fake_neuron(1, ip="9.9.9.9", country="US")
    miners = [fake_miner(1, ip="1.1.1.1", country="US")]
    neurons = {neuron.hotkey: neuron}
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    updated_miners, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    assert len(updated_miners) == 1
    assert len(reset_miners) == 0


@pytest.mark.asyncio
async def test_sync_miners_returns_reset_miners_on_ip_change_and_different_country():
    db = AsyncMock()
    neuron = fake_neuron(1, ip="5.5.5.5", country="US")
    neurons = {neuron.hotkey: neuron}
    miner = fake_miner(1, ip="1.1.1.1", country="FR")
    miners = [miner]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    updated_miners, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    assert len(updated_miners) == 1
    assert len(reset_miners) == 1
    assert reset_miners[0].uid == 1
    assert reset_miners[0].ip == "1.1.1.1"


@pytest.mark.asyncio
async def test_sync_miners_returns_reset_miners_on_hotkey_change():
    db = AsyncMock()
    neuron = fake_neuron(1, ip="1.1.1.1", hotkey="new-hk")
    neurons = {neuron.hotkey: neuron}
    miner = fake_miner(1, ip="1.1.1.1")
    miners = [miner]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    updated_miners, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    assert len(updated_miners) == 1
    assert len(reset_miners) == 1
    assert reset_miners[0].uid == 1
    assert reset_miners[0].hotkey == "hk"
    assert reset_miners[0].ip == "1.1.1.1"


@pytest.mark.asyncio
async def test_sync_miners_returns_reset_miners_on_hotkey_and_ip_change():
    db = AsyncMock()
    neuron = fake_neuron(1, ip="5.5.5.5", hotkey="new-hk")
    neurons = {neuron.hotkey: neuron}
    miner = fake_miner(1, ip="1.1.1.1")
    miners = [miner]
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    updated_miners, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    assert len(updated_miners) == 1
    assert len(reset_miners) == 1
    assert reset_miners[0].uid == 1
    assert reset_miners[0].hotkey == "hk"
    assert reset_miners[0].ip == "1.1.1.1"


@pytest.mark.asyncio
async def test_sync_miners_no_reset_on_new_miner():
    db = AsyncMock()
    neurons = {"hk1": fake_neuron(1, hotkey="new-hk")}
    miners = []
    validator = fake_neuron(999, country="US")
    locations = ["US", "CA"]

    updated_miners, reset_miners = await sync_miners(
        db, neurons, miners, validator, locations, min_stake=1000
    )

    assert len(updated_miners) == 1
    assert len(reset_miners) == 0
