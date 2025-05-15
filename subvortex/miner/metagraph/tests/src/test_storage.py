import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from subvortex.miner.metagraph.src.storage import Storage
import subvortex.core.metagraph.models as scmm
import subvortex.miner.metagraph.src.settings as scms


class DummySettings(scms.Settings):
    redis_host = "localhost"
    redis_port = 6379
    redis_index = 0
    redis_password = "secret"
    KEY_PREFIX = "test"
    LOGGING_NAME = "test_logger"


@pytest.fixture
def storage():
    settings = DummySettings()
    s = Storage(settings)
    s.client = MagicMock()
    s.client.set = AsyncMock()
    s.client.get = AsyncMock()
    s.client.hgetall = AsyncMock()
    s.client.keys = AsyncMock()
    s.client.xadd = AsyncMock()
    return s


class AsyncContextManager:
    def __init__(self, mock):
        self.mock = mock

    async def __aenter__(self):
        return self.mock

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_set_neurons(storage):
    neurons = [scmm.Neuron(hotkey="hk1"), scmm.Neuron(hotkey="hk2")]
    with patch.object(
        scmm.Neuron, "to_dict", side_effect=lambda n: {"hotkey": n.hotkey}
    ):
        mock_pipe = AsyncMock()
        storage.client.pipeline.return_value = AsyncContextManager(mock_pipe)

        await storage.set_neurons(neurons)

        assert mock_pipe.hmset.call_count == 2
        mock_pipe.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_neuron_found(storage):
    data = {"hotkey": "hk1"}
    storage.client.hgetall.return_value = data

    with patch.object(scmm.Neuron, "from_dict", return_value=scmm.Neuron(hotkey="hk1")):
        result = await storage.get_neuron("hk1")
        assert result.hotkey == "hk1"


@pytest.mark.asyncio
async def test_get_neuron_not_found(storage):
    storage.client.hgetall.return_value = None
    result = await storage.get_neuron("hk1")
    assert result is None


@pytest.mark.asyncio
async def test_get_neurons(storage):
    storage.client.keys.return_value = ["test:neuron:hk1", "test:neuron:hk2"]
    storage.client.pipeline.return_value = pipe = AsyncMock()
    pipe.execute.return_value = [{"hotkey": "hk1"}, {"hotkey": "hk2"}]

    with patch.object(
        scmm.Neuron, "from_dict", side_effect=lambda d: scmm.Neuron(hotkey=d["hotkey"])
    ):
        neurons = await storage.get_neurons()
        assert len(neurons) == 2
        assert neurons[0].hotkey == "hk1"
        assert neurons[1].hotkey == "hk2"


@pytest.mark.asyncio
async def test_mark_as_ready(storage):
    await storage.mark_as_ready()
    storage.client.set.assert_awaited_once_with("sv:state:metagraph", "ready")


@pytest.mark.asyncio
async def test_mark_as_unready(storage):
    await storage.mark_as_unready()
    storage.client.set.assert_awaited_once_with("sv:state:metagraph", "unready")


@pytest.mark.asyncio
async def test_notify_state(storage):
    storage.client.get.return_value = "ready"
    await storage.notify_state()
    storage.client.xadd.assert_awaited_once_with("metagraph", {"state": "ready"})
