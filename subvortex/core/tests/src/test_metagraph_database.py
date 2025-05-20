import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import subvortex.core.model.neuron.neuron as scmm
import subvortex.core.metagraph.settings as scms

from subvortex.core.metagraph.database import NeuronDatabase


class DummySettings(scms.Settings):
    database_host = "localhost"
    database_port = 6379
    database_index = 0
    database_password = "secret"


@pytest.fixture
def database():
    settings = DummySettings()
    s = NeuronDatabase(settings)

    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.set = AsyncMock()
    mock_redis.get = AsyncMock()
    mock_redis.hgetall = AsyncMock()
    mock_redis.keys = AsyncMock()
    mock_redis.xadd = AsyncMock()
    mock_redis.delete = AsyncMock()

    # Async pipeline mock
    mock_pipe = MagicMock()
    mock_pipe.hmset = AsyncMock()
    mock_pipe.hgetall = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[{"hotkey": "hk1"}, {"hotkey": "hk2"}])

    mock_pipeline_cm = MagicMock()
    mock_pipeline_cm.__aenter__ = AsyncMock(return_value=mock_pipe)
    mock_pipeline_cm.__aexit__ = AsyncMock(return_value=False)

    mock_redis.pipeline = MagicMock(return_value=mock_pipeline_cm)

    # Patch the database and connection
    s.database = mock_redis
    s.ensure_connection = AsyncMock()

    # Patch _get_migration_status to return mock version
    s._get_migration_status = AsyncMock(return_value=(None, ["2.1.0"]))

    # Patch the model methods
    mock_model = MagicMock()
    mock_model.write_all = AsyncMock()
    mock_model.read = AsyncMock(return_value=scmm.Neuron(hotkey="hk1"))
    mock_model.read_all = AsyncMock(
        return_value=[scmm.Neuron(hotkey="hk1"), scmm.Neuron(hotkey="hk2")]
    )
    mock_model.delete_all = AsyncMock()
    s.models["neuron"]["2.1.0"] = mock_model
    s._mock_model = mock_model  # optional for assertions

    return s


class AsyncContextManager:
    def __init__(self, mock):
        self.mock = mock

    async def __aenter__(self):
        return self.mock

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_update_neurons(database):
    neurons = [scmm.Neuron(hotkey="hk1"), scmm.Neuron(hotkey="hk2")]
    await database.update_neurons(neurons)

    database._mock_model.write_all.assert_awaited_once_with(database.database, neurons)


@pytest.mark.asyncio
async def test_get_neuron_found(database):
    neuron = await database.get_neuron("hk1")
    assert neuron is not None
    assert neuron.hotkey == "hk1"
    database._mock_model.read.assert_awaited_once_with(database.database, "hk1")


@pytest.mark.asyncio
async def test_get_neurons(database):
    neurons = await database.get_neurons()
    assert len(neurons) == 2
    assert neurons[0].hotkey == "hk1"
    assert neurons[1].hotkey == "hk2"
    database._mock_model.read_all.assert_awaited_once_with(database.database)


@pytest.mark.asyncio
async def test_remove_neurons(database):
    neurons = [scmm.Neuron(hotkey="hk1")]
    await database.remove_neurons(neurons)
    database._mock_model.delete_all.assert_awaited_once_with(database.database, neurons)


@pytest.mark.asyncio
async def test_get_last_updated_success(database):
    database.database.get.return_value = b"123456"

    with patch(
        "subvortex.core.metagraph.database.decode_hash", return_value="123456"
    ):
        block = await database.get_last_updated()

    assert block == 123456
    database.database.get.assert_awaited_once_with("sv:state:neuron:last_updated")


@pytest.mark.asyncio
async def test_get_last_updated_failure(database):
    database.database.get.side_effect = Exception("Redis error")

    with patch(
        "subvortex.core.metagraph.database.decode_hash", return_value="0"
    ):
        block = await database.get_last_updated()

    assert block == 0


@pytest.mark.asyncio
async def test_set_last_updated_failure(database):
    database.database.set.side_effect = Exception("fail")
    await database.set_last_updated(9001)
    # The error is logged, not raised
    database.database.set.assert_awaited_once_with(
        "sv:state:neuron:last_updated", "9001"
    )


def test__key(database):
    assert database._key("neuron:hk1") == "sv:neuron:hk1"


@pytest.mark.asyncio
async def test__set_state_success(database):
    await database._set_state("testing")
    database.database.set.assert_awaited_with("sv:state:metagraph", "testing")


@pytest.mark.asyncio
async def test__set_state_failure(database):
    database.database.set.side_effect = Exception("set failed")
    await database._set_state("failcase")
