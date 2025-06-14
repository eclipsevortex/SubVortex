# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from subvortex.core.model.schedule import ScheduleModel210, Schedule
from subvortex.core.model.challenge import ChallengeModel210, Challenge
from subvortex.validator.core.model.miner import MinerModel211, Miner
from subvortex.validator.core.challenger.database import Database


class DummySettings:
    key_prefix = "sv"
    logging_name = "test"
    redis_url = "redis://localhost:6379/0"


@pytest_asyncio.fixture
async def db():
    db = Database(DummySettings())
    db.ensure_connection = AsyncMock()
    db.get_client = AsyncMock()
    client = AsyncMock()
    db.get_client.return_value = client
    return db


# === Schedule Tests ===

@pytest.mark.asyncio
async def test_add_schedule_success(db):
    # Arrange
    version = ScheduleModel210().version
    schedule = Schedule.create(0, 1, 100, 200, 1000, 1100, "FR")
    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["schedule"][version].write = AsyncMock()

    # Act
    await db.add_schedule(schedule)

    # Assert
    db.models["schedule"][version].write.assert_called_once_with(db.get_client.return_value, schedule)


@pytest.mark.asyncio
async def test_add_schedule_missing_model_skipped(db):
    # Arrange
    db._get_migration_status = AsyncMock(return_value=("2.0.0", ["3.0.0"]))  # Not registered
    schedule = Schedule.create(0, 1, 100, 200, 1000, 1100, "FR")

    # Act & Assert: Should not raise even if model is missing
    await db.add_schedule(schedule)


@pytest.mark.asyncio
async def test_add_schedule_write_fails_logs_error(db):
    # Arrange
    version = ScheduleModel210().version
    schedule = Schedule.create(0, 1, 100, 200, 1000, 1100, "FR")
    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["schedule"][version].write = AsyncMock(side_effect=Exception("fail"))

    # Act
    await db.add_schedule(schedule)

    # Assert: no exception raised, log expected (log check omitted here)


def test_schedule_properties_and_dict_conversion():
    # Arrange
    s = Schedule.create(3, 4, 100, 200, 1000, 1100, "DE")

    # Act
    d = s.to_dict()
    restored = Schedule.from_dict(d)

    # Assert
    assert s.id == "4:100:200:1000:1100"
    assert s.instance == 4
    assert s.step_index == 4
    assert s.instance_index == 5
    assert d == {
        "index": 3,
        "instance": 4,
        "cycle_start": 100,
        "cycle_end": 200,
        "block_start": 1000,
        "block_end": 1100,
        "country": "DE",
    }
    assert restored == s


def test_schedule_equality_and_inequality():
    # Arrange
    s1 = Schedule.create(0, 1, 10, 20, 30, 40, "US")
    s2 = Schedule.create(0, 1, 10, 20, 30, 40, "US")
    s3 = Schedule.create(0, 1, 10, 20, 30, 41, "US")

    # Act & Assert
    assert s1 == s2
    assert s1 != s3


# === Challenge Tests ===

@pytest.mark.asyncio
async def test_add_challenge_success(db):
    # Arrange
    version = ChallengeModel210().version
    challenge = Challenge.create("abc-123", 0.25, ("params", "blockhash", "value"))
    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["challenge"][version].write = AsyncMock()

    # Act
    await db.add_challenge(challenge)

    # Assert
    db.models["challenge"][version].write.assert_called_once_with(db.get_client.return_value, challenge)


@pytest.mark.asyncio
async def test_add_challenge_missing_model_skipped(db):
    # Arrange
    db._get_migration_status = AsyncMock(return_value=("2.0.0", ["3.0.0"]))
    challenge = Challenge.create("id", 1.0, ("x", "y", "z"))

    # Act & Assert
    await db.add_challenge(challenge)  # Should not raise


@pytest.mark.asyncio
async def test_add_challenge_write_fails_logs_error(db):
    # Arrange
    version = ChallengeModel210().version
    challenge = Challenge.create("fail-id", 0.5, ("x", "y", "z"))
    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["challenge"][version].write = AsyncMock(side_effect=Exception("boom"))

    # Act
    await db.add_challenge(challenge)

    # Assert: no exception raised


def test_challenge_properties_and_dict_conversion():
    # Arrange
    c = Challenge.create("cid", 1.25, ("p", "h", "v"))

    # Act
    d = c.to_dict()
    restored = Challenge.from_dict(d)

    # Assert
    assert c.id == "cid"
    assert d == {
        "step_id": "cid",
        "params": "p",
        "block_hash": "h",
        "value": "v",
        "process_time": 1.25,
    }
    assert restored.to_dict() == d


def test_challenge_with_none_tuple():
    # Arrange
    c = Challenge.create("nid", 0.0, None)
    print(c)

    # Act
    d = c.to_dict()

    # Assert
    assert c.params is None
    assert c.block_hash is None
    assert c.value is None
    assert d == {
        "step_id": "nid",
        "params": "",
        "block_hash": "",
        "value": "",
        "process_time": 0.0,
    }


# === Miner Tests ===

@pytest.mark.asyncio
async def test_get_miners_success(db):
    # Arrange
    version = MinerModel211().version
    miners = {"hk": Miner(hotkey="hk", uid=1)}
    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["miner"][version].read_all = AsyncMock(return_value=miners)

    # Act
    result = await db.get_miners()

    # Assert
    assert result == miners
    db.models["miner"][version].read_all.assert_called_once_with(db.get_client.return_value)


@pytest.mark.asyncio
async def test_get_miners_all_versions_fail(db):
    # Arrange
    version = MinerModel211().version
    db._get_migration_status = AsyncMock(return_value=(version, [version]))
    db.models["miner"][version].read_all = AsyncMock(side_effect=Exception("fail"))

    # Act
    result = await db.get_miners()

    # Assert
    assert result is None
