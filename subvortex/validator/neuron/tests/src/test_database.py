
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from subvortex.validator.neuron.src.models.selection import SelectionModel200
from subvortex.validator.neuron.src.models.miner import MinerModel210, Miner
from subvortex.core.model.neuron import NeuronModel210, Neuron
from subvortex.validator.neuron.src.database import Database


class DummySettings:
    key_prefix = "sv"
    logging_name = "test"
    database_host="localhost"
    database_port=6379
    database_index=0
    database_password=None


@pytest_asyncio.fixture
async def db():
    db = Database(DummySettings())
    db.ensure_connection = AsyncMock()
    db.get_client = AsyncMock()
    client = AsyncMock()
    db.get_client.return_value = client
    return db


@pytest.mark.asyncio
async def test_get_selected_miners_success(db):
    version = SelectionModel200().version
    expected_uids = [1, 5, 10]

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["selection"][version].read = AsyncMock(return_value=expected_uids)

    result = await db.get_selected_miners("hotkey1")

    assert result == expected_uids
    db.models["selection"][version].read.assert_called_once()


@pytest.mark.asyncio
async def test_set_selection_miners_calls_write(db):
    version = SelectionModel200().version
    uids = [2, 3, 7]

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["selection"][version].write = AsyncMock()

    await db.set_selection_miners("hotkey2", uids)

    db.models["selection"][version].write.assert_called_once_with(
        db.get_client.return_value, "hotkey2", uids
    )


@pytest.mark.asyncio
async def test_get_neuron_success(db):
    version = NeuronModel210().version
    neuron = Neuron(hotkey="hk", uid=1)

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["neuron"][version].read = AsyncMock(return_value=neuron)

    result = await db.get_neuron("hk")
    assert result == neuron
    db.models["neuron"][version].read.assert_called_once()


@pytest.mark.asyncio
async def test_get_neurons_success(db):
    version = NeuronModel210().version
    neurons = {"hk": Neuron(hotkey="hk", uid=1)}

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["neuron"][version].read_all = AsyncMock(return_value=neurons)

    result = await db.get_neurons()
    assert result == neurons
    db.models["neuron"][version].read_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_miner_success(db):
    version = MinerModel210().version
    miner = Miner(hotkey="hk", uid=1)

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["miner"][version].read = AsyncMock(return_value=miner)

    result = await db.get_miner("hk")
    assert result == miner
    db.models["miner"][version].read.assert_called_once()


@pytest.mark.asyncio
async def test_get_miners_success(db):
    version = MinerModel210().version
    miners = {"hk": Miner(hotkey="hk", uid=1)}

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["miner"][version].read_all = AsyncMock(return_value=miners)

    result = await db.get_miners()
    assert result == miners
    db.models["miner"][version].read_all.assert_called_once()


@pytest.mark.asyncio
async def test_add_miner_calls_write(db):
    version = MinerModel210().version
    miner = Miner(hotkey="hk", uid=1)

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["miner"][version].write = AsyncMock()

    await db.add_miner(miner)
    db.models["miner"][version].write.assert_called_once_with(db.get_client.return_value, miner)


@pytest.mark.asyncio
async def test_update_miners_batch_success(db):
    version = MinerModel210().version
    miners = [Miner(hotkey="hk", uid=1)]

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["miner"][version].write_all = AsyncMock()

    await db.update_miners(miners)
    db.models["miner"][version].write_all.assert_called_once_with(db.get_client.return_value, miners)


@pytest.mark.asyncio
async def test_remove_miner_calls_delete(db):
    version = MinerModel210().version
    miner = Miner(hotkey="hk", uid=1)

    db.models["miner"] = {version: MinerModel210()}
    db.models["miner"][version].delete = AsyncMock()

    await db.remove_miner(miner)
    db.models["miner"][version].delete.assert_called_once_with(db.get_client.return_value, miner)


@pytest.mark.asyncio
async def test_get_last_update_success(db):
    db.get_client.return_value.get = AsyncMock(return_value=b"1000")

    result = await db.get_neuron_last_updated()
    assert result == 1000


@pytest.mark.asyncio
async def test_get_migration_status_returns_active_versions(db):
    db.models["selection"] = {"2.0.0": SelectionModel200()}
    db.get_client.return_value.get = AsyncMock(return_value=b"new")

    latest, active = await db._get_migration_status("selection")
    assert latest == "2.0.0"
    assert active == ["2.0.0"]
    db.get_client.return_value.get.assert_called_once_with("migration_mode:2.0.0")


@pytest.mark.asyncio
async def test_get_migration_status_fallback(db):
    db.models["selection"] = {
        "2.0.0": SelectionModel200(),
        "2.1.0": SelectionModel200(),
    }
    db.get_client.return_value.get = AsyncMock(return_value=None)

    latest, active = await db._get_migration_status("selection")
    assert latest == "2.1.0"
    assert active == ["2.1.0"]
