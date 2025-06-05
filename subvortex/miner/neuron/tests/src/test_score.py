import pytest
import json
import os
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory

from subvortex.miner.neuron.src.score import save_scores
from subvortex.miner.neuron.src.models.score import Score


class FakeSynapse:
    validator_uid = 123
    block = 100
    rank = 0.5
    availability = 1.0
    latency = 0.2
    reliability = 0.9
    distribution = 0.8
    score = 0.95
    moving_score = 0.93
    penalty_factor = None


@pytest.fixture
def default_data():
    return {
        "score_saving_enabled": True,
        "score_saving_target": "json",
        "score_saving_json_path": None,
        "score_max_entries": 5,
    }


@pytest.mark.asyncio
async def test_score_saving_disabled_json(default_data):
    with TemporaryDirectory() as tmp:
        settings = mock.Mock(**{**default_data, "score_saving_enabled": False})
        synapse = FakeSynapse()
        database = mock.AsyncMock()

        await save_scores(settings, database, synapse, path=tmp)

        scores_path = os.path.join(tmp, "scores.json")
        assert not os.path.exists(
            scores_path
        ), "scores.json should not exist if saving is disabled"


@pytest.mark.asyncio
async def test_score_saving_disabled_redis(default_data):
    settings = mock.Mock(
        **{
            **default_data,
            "score_saving_enabled": False,
            "score_saving_target": "redis",
        }
    )
    synapse = FakeSynapse()
    database = mock.AsyncMock()

    await save_scores(settings, database, synapse, path="/tmp")

    database.save_scores.assert_not_called()
    database.prune_scores.assert_not_called()


@pytest.mark.asyncio
async def test_save_score_json_no_file(default_data):
    with TemporaryDirectory() as tmp:
        settings = mock.Mock(**default_data)
        synapse = FakeSynapse()

        await save_scores(settings, mock.Mock(), synapse, path=tmp)

        fpath = os.path.join(tmp, "scores.json")
        with open(fpath) as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert data[0]["vuid"] == 123


@pytest.mark.asyncio
async def test_save_score_json_existing_valid_list(default_data):
    with TemporaryDirectory() as tmp:
        scores_path = Path(tmp) / "scores.json"

        # Create realistic old scores
        old_scores = [
            {
                "vuid": i,
                "block": 90 + i,
                "rank": 0.1 * i,
                "availability_score": 0.9,
                "latency_score": 0.1,
                "reliability_score": 0.8,
                "distribution_score": 0.7,
                "score": 0.5 + 0.01 * i,
                "moving_score": 0.4 + 0.01 * i,
                "penalty_factor": -1,
            }
            for i in range(10)
        ]
        scores_path.write_text(json.dumps(old_scores, indent=2))

        settings = mock.Mock(**default_data)
        synapse = FakeSynapse()

        await save_scores(settings, mock.Mock(), synapse, path=tmp)

        result = json.loads(scores_path.read_text())

        # Ensure new score was added
        assert len(result) == settings.score_max_entries
        assert any(entry.get("vuid") == 123 for entry in result)

        # Ensure blocks are the most recent X blocks (should be 96 to 100 if max_entries is 5)
        blocks = [entry["block"] for entry in result]
        expected_blocks = list(range(100, 100 - settings.score_max_entries, -1))
        assert blocks == expected_blocks, f"Expected {expected_blocks}, got {blocks}"


@pytest.mark.asyncio
async def test_save_score_json_existing_not_list(default_data):
    with TemporaryDirectory() as tmp:
        scores_path = Path(tmp) / "scores.json"

        # Valid JSON, but not a list
        scores_path.write_text(json.dumps({"invalid": True}))

        settings = mock.Mock(**default_data)
        synapse = FakeSynapse()

        await save_scores(settings, mock.Mock(), synapse, path=tmp)

        result = json.loads(scores_path.read_text())
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["vuid"] == 123


@pytest.mark.asyncio
async def test_save_score_json_invalid_json(default_data):
    with TemporaryDirectory() as tmp:
        scores_path = Path(tmp) / "scores.json"

        # Malformed JSON
        scores_path.write_text("{invalid_json: true")

        settings = mock.Mock(**default_data)
        synapse = FakeSynapse()

        await save_scores(settings, mock.Mock(), synapse, path=tmp)

        result = json.loads(scores_path.read_text())
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["vuid"] == 123


@pytest.mark.asyncio
async def test_save_score_redis(default_data):
    settings = mock.Mock(**{**default_data, "score_saving_target": "redis"})
    database = mock.AsyncMock()
    synapse = FakeSynapse()

    with mock.patch(
        "subvortex.miner.neuron.src.score.Score.from_dict"
    ) as mock_from_dict:
        mock_score = mock.Mock(spec=Score)
        mock_from_dict.return_value = mock_score

        await save_scores(settings, database, synapse, path="/tmp")

        mock_from_dict.assert_called_once()
        database.save_scores.assert_awaited_once_with(mock_score)
        database.prune_scores.assert_awaited_once()


@pytest.mark.asyncio
async def test_json_write_exception_logged(default_data):
    with mock.patch("builtins.open", side_effect=IOError("boom")):
        settings = mock.Mock(**default_data)
        synapse = FakeSynapse()

        # Patch logging
        with mock.patch("bittensor.utils.btlogging.logging.error") as mock_log:
            await save_scores(settings, mock.Mock(), synapse, path="/tmp")
            mock_log.assert_called_once()
            assert "Failed to save score" in mock_log.call_args[0][0]
