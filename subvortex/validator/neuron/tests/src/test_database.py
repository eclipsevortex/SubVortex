import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from subvortex.validator.neuron.src.models.statistics import StatisticModel200
from subvortex.validator.neuron.src.models.selection import SelectionModel200
from subvortex.validator.neuron.src.database import Database


class DummySettings:
    logging_name = "test"
    redis_url = "redis://localhost:6379/0"


@pytest_asyncio.fixture
async def db():
    db = Database(DummySettings())
    db.ensure_connection = AsyncMock()
    db.database = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_hotkey_statistics_success(db):
    mock_data = {"score": 0.75}
    version = StatisticModel200().version

    # Patch read method of model
    db.models["statistic"][version].read = AsyncMock(return_value=mock_data)
    db._get_migration_status = AsyncMock(return_value=(version, [version]))

    result = await db.get_hotkey_statistics("abc123")

    assert result == mock_data
    db.models["statistic"][version].read.assert_called_once()


@pytest.mark.asyncio
async def test_update_hotkey_statistics_calls_write(db):
    version = StatisticModel200().version
    data = {"score": 0.92}

    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["statistic"][version].write = AsyncMock()

    await db.update_hotkey_statistics("abc123", data)

    db.models["statistic"][version].write.assert_called_once_with(
        db.database, "abc123", data
    )


@pytest.mark.asyncio
async def test_remove_hotkey_statistics_calls_delete(db):
    version = StatisticModel200().version
    db.models["statistic"][version].delete = AsyncMock()

    await db.remove_hotkey_stastitics("abc123")

    db.models["statistic"][version].delete.assert_called_once_with(
        db.database, "abc123"
    )


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
        db.database, "hotkey2", uids
    )


@pytest.mark.asyncio
async def test_get_migration_status_returns_active_versions(db):
    db.models["statistic"] = {"200": StatisticModel200()}
    db.database.get = AsyncMock(return_value=b"new")

    latest, active = await db._get_migration_status("statistic")

    assert latest == "200"
    assert active == ["200"]
    db.database.get.assert_called_once_with("migration_mode:200")


@pytest.mark.asyncio
async def test_get_migration_status_fallback_no_migration_mode(db):
    # Simulate two versions with no migration_mode set
    db.models["statistic"] = {
        "2.0.0": StatisticModel200(),
        "2.1.0": StatisticModel200(),
    }

    # No value returned from redis for either version
    db.database.get = AsyncMock(return_value=None)

    latest, active = await db._get_migration_status("statistic")

    assert latest == "2.1.0"
    assert active == ["2.1.0"]


@pytest.mark.asyncio
async def test_get_migration_status_fallback_when_none_marked_new(db):
    db.models["selection"] = {
        "2.0.0": SelectionModel200(),
        "2.1.0": SelectionModel200(),
    }

    async def fake_get(key):
        return b"old" if "2.0.0" in key or "2.1.0" in key else None

    db.database.get = AsyncMock(side_effect=fake_get)

    latest, active = await db._get_migration_status("selection")

    assert latest == "2.1.0"
    assert active == ["2.1.0"]
