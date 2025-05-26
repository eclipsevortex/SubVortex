import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import subvortex.core.model.neuron.neuron as scmm
import subvortex.core.metagraph.settings as scms


@pytest.fixture
def mock_database():
    database = AsyncMock()
    database.get_neurons.return_value = []
    return database


@pytest.fixture
def mock_subtensor():
    return AsyncMock()


@pytest.fixture
def mock_metagraph():
    mock = AsyncMock()
    mock.neurons = []
    return mock


@pytest.fixture
def database_with_mocked_redis():
    from subvortex.core.metagraph.database import NeuronDatabase
    from subvortex.miner.metagraph.src.settings import Settings

    database = NeuronDatabase(Settings.create())

    with patch.object(database, "client", new_callable=AsyncMock):
        yield database


@pytest.fixture
def observer(mock_database, mock_subtensor, mock_metagraph):
    from subvortex.core.metagraph.metagraph import MetagraphObserver

    return MetagraphObserver(
        settings=scms.Settings.create(),
        database=mock_database,
        subtensor=mock_subtensor,
        metagraph=mock_metagraph,
    )


@pytest.mark.asyncio
async def test_notify_if_needed(observer):
    # Arrange
    observer.database.mark_as_ready = AsyncMock()
    observer.database.notify_state = AsyncMock()
    result = await observer._notify_if_needed(False)

    # Action
    assert result is True

    # Assert
    observer.database.mark_as_ready.assert_called_once()
    observer.database.notify_state.assert_called_once()


@pytest.mark.asyncio
async def test_notify_if_not_needed(observer):
    # Arrange
    observer.database.mark_as_ready = AsyncMock()
    observer.database.notify_state = AsyncMock()
    result = await observer._notify_if_needed(True)

    # Action
    assert result is True

    # Assert
    observer.database.mark_as_ready.assert_not_called()
    observer.database.notify_state.assert_not_called()


@pytest.mark.asyncio
async def test_has_new_neuron_registered_same_count(observer):
    observer.subtensor = AsyncMock()
    with (
        patch(
            "subvortex.core.core_bittensor.subtensor.get_number_of_registration",
            return_value=5,
        ),
        patch(
            "subvortex.core.core_bittensor.subtensor.get_next_adjustment_block",
            return_value=100,
        ),
    ):

        # Action
        result, count = await observer._has_new_neuron_registered(5, 99)

        # Assert
        assert result is False
        assert count == 5


@pytest.mark.asyncio
async def test_has_new_neuron_registered_reset(observer):
    observer.subtensor = AsyncMock()
    with (
        patch(
            "subvortex.core.core_bittensor.subtensor.get_number_of_registration",
            return_value=5,
        ),
        patch(
            "subvortex.core.core_bittensor.subtensor.get_next_adjustment_block",
            return_value=100,
        ),
    ):

        # Action
        result, count = await observer._has_new_neuron_registered(5, 100)

        # Assert
        assert result is False
        assert count == 0


@pytest.mark.asyncio
async def test_has_new_neuron_registered_new(observer):
    observer.subtensor = AsyncMock()
    with patch(
        "subvortex.core.core_bittensor.subtensor.get_number_of_registration",
        return_value=6,
    ):

        # Action
        result, count = await observer._has_new_neuron_registered(5, 101)

        # Assert
        assert result is True
        assert count == 6


@pytest.mark.asyncio
async def test_has_neuron_ip_changed(observer):
    observer.subtensor = AsyncMock()
    old_axons = {"hk1": "1.1.1.1"}

    with patch(
        "subvortex.core.core_bittensor.subtensor.get_axons",
        return_value={"hk1": "1.1.1.2"},
    ):
        # Action
        changed, new_axons = await observer._has_neuron_ip_changed(old_axons)

        # Assert
        assert changed is True
        assert new_axons["hk1"] == "1.1.1.2"


@pytest.mark.asyncio
async def test_has_neuron_ip_unchanged(observer):
    observer.subtensor = AsyncMock()
    old_axons = {"hk1": "1.1.1.1"}

    with patch(
        "subvortex.core.core_bittensor.subtensor.get_axons",
        return_value={"hk1": "1.1.1.1"},
    ):
        # Action
        changed, new_axons = await observer._has_neuron_ip_changed(old_axons)

        # Assert
        assert changed is False
        assert new_axons["hk1"] == "1.1.1.1"


@pytest.mark.asyncio
async def test_resync_updates_neurons(observer):
    from subvortex.core.model.neuron.neuron import Neuron

    fake_proto = MagicMock()
    fake_proto.uid = 1
    fake_proto.axon_info.ip = "1.2.3.4"
    fake_proto.hotkey = "hotkey123"
    fake_proto.incentive = 0.1

    new_neuron = Neuron.from_proto = MagicMock(
        return_value=Neuron(
            uid=1, ip="1.2.3.4", hotkey="hotkey123", country="US", incentive=0.2
        )
    )

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(return_value={})
    observer.database.update_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=new_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value="US"),
    ):
        axons, _ = await observer._resync()
        assert "hotkey123" in axons
        observer.database.update_neurons.assert_called_once_with([new_neuron])
        assert axons["hotkey123"] == "1.2.3.4"


@pytest.mark.asyncio
async def test_start_and_stop(observer):
    # Mock all internal behavior
    observer._resync = AsyncMock(return_value=({"hk": "1.1.1.1"}, False))
    observer._notify_if_needed = AsyncMock(return_value=True)
    observer._has_new_neuron_registered = AsyncMock(return_value=(True, 1))
    observer._has_neuron_ip_changed = AsyncMock(return_value=(False, {}))
    observer.subtensor.get_current_block = AsyncMock(return_value=123)

    # Force exit after one loop using `should_exit.set()` inside the loop
    # Patch wait_for_block so it returns immediately
    with patch(
        "subvortex.core.core_bittensor.subtensor.wait_for_block", new_callable=AsyncMock
    ) as mock_wait:

        async def wait_for_block_mock(*args, **kwargs):
            await asyncio.sleep(0.1)
            return True

        mock_wait.side_effect = wait_for_block_mock

        task = asyncio.create_task(observer.start())
        await asyncio.sleep(0.1)
        await observer.stop()

        # Await the start task to finish gracefully
        await asyncio.wait_for(task, timeout=1.0)

    # Assertions
    assert observer.finished.is_set()
    observer._resync.assert_called_once()
    observer._notify_if_needed.assert_called_once()
    observer._has_new_neuron_registered.assert_called_once()


@pytest.mark.asyncio
async def test_resync_no_neuron_change(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 1
    fake_proto.axon_info.ip = "1.2.3.4"
    fake_proto.hotkey = "hotkey123"

    stored_neuron = scmm.Neuron(uid=1, ip="1.2.3.4", hotkey="hotkey123", country="US")

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={stored_neuron.hotkey: stored_neuron}
    )
    observer.database.update_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=stored_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value="FR"),
    ):
        axons, _ = await observer._resync()

        observer.database.remove_neurons.assert_not_called()
        observer.database.update_neurons.assert_not_called()
        assert axons["hotkey123"] == "1.2.3.4"


@pytest.mark.asyncio
async def test_resync_neuron_ip_changed(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 1
    fake_proto.axon_info.ip = "9.9.9.9"
    fake_proto.hotkey = "hotkey123"

    old_neuron = scmm.Neuron(uid=1, ip="1.1.1.1", hotkey="hotkey123", country="US")
    new_neuron = scmm.Neuron(uid=1, ip="9.9.9.9", hotkey="new_hotkey", country="FR")

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={old_neuron.hotkey: old_neuron}
    )
    observer.database.update_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=new_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value="FR"),
    ):
        axons, _ = await observer._resync()
        observer.database.remove_neurons.assert_called_once_with([old_neuron])
        observer.database.update_neurons.assert_called_once_with([new_neuron])
        assert axons["hotkey123"] == "9.9.9.9"


@pytest.mark.asyncio
async def test_resync_hotkey_changed(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 1
    fake_proto.axon_info.ip = "1.1.1.1"
    fake_proto.hotkey = "new_hotkey"

    old_neuron = scmm.Neuron(uid=1, ip="1.1.1.1", hotkey="old_hotkey", country="US")
    new_neuron = scmm.Neuron(uid=1, ip="1.1.1.1", hotkey="new_hotkey", country="US")

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={old_neuron.hotkey: old_neuron}
    )
    observer.database.update_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=new_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value="US"),
    ):
        axons, _ = await observer._resync()
        observer.database.remove_neurons.assert_called_once_with([old_neuron])
        observer.database.update_neurons.assert_called_once_with([new_neuron])
        assert axons["new_hotkey"] == "1.1.1.1"


@pytest.mark.asyncio
async def test_resync_neuron_not_in_database(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 42
    fake_proto.axon_info.ip = "5.5.5.5"
    fake_proto.hotkey = "new_hotkey"

    new_neuron = scmm.Neuron(uid=42, ip="5.5.5.5", hotkey="new_hotkey", country="US")

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(return_value={})
    observer.database.update_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=new_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value="FR"),
    ):
        axons, _ = await observer._resync()
        observer.database.remove_neurons.assert_not_called()
        observer.database.update_neurons.assert_called_once_with([new_neuron])
        assert axons["new_hotkey"] == "5.5.5.5"


@pytest.mark.asyncio
async def test_resync_neuron_with_no_country_not_in_database(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 42
    fake_proto.axon_info.ip = "5.5.5.5"
    fake_proto.hotkey = "new_hotkey"

    new_neuron = scmm.Neuron(uid=42, ip="5.5.5.5", hotkey="new_hotkey", country=None)

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(return_value={})
    observer.database.update_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=new_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value=None),
    ):
        axons, _ = await observer._resync()
        observer.database.remove_neurons.assert_not_called()
        observer.database.update_neurons.assert_called_once_with([new_neuron])
        assert axons["new_hotkey"] == "5.5.5.5"


@pytest.mark.asyncio
async def test_resync_country_not_updated_if_ip_is_same(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 99
    fake_proto.axon_info.ip = "2.2.2.2"
    fake_proto.hotkey = "hotkey99"

    stored_neuron = scmm.Neuron(uid=99, ip="2.2.2.2", hotkey="hotkey99", country="US")

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={stored_neuron.hotkey: stored_neuron}
    )
    observer.database.update_neurons = AsyncMock()

    with patch(
        "subvortex.core.model.neuron.neuron.Neuron.from_proto",
        return_value=stored_neuron,
    ):
        axons, _ = await observer._resync()

    observer.database.remove_neurons.assert_not_called()
    observer.database.update_neurons.assert_not_called()
    assert axons["hotkey99"] == "2.2.2.2"


@pytest.mark.asyncio
@patch("bittensor.utils.btlogging.logging.debug")
async def test_resync_removes_old_hotkey(mock_debug, observer):
    fake_proto = MagicMock()
    fake_proto.uid = 1
    fake_proto.axon_info.ip = "3.3.3.3"
    fake_proto.hotkey = "new_hotkey"

    old_neuron = scmm.Neuron(uid=1, ip="3.3.3.3", hotkey="old_hotkey", country="US")
    new_neuron = scmm.Neuron(uid=1, ip="3.3.3.3", hotkey="new_hotkey", country=None)

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={old_neuron.hotkey: old_neuron}
    )
    observer.database.update_neurons = AsyncMock()
    observer.database.remove_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=new_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value="US"),
    ):
        axons, _ = await observer._resync()

    observer.database.remove_neurons.assert_called_once_with([old_neuron])
    observer.database.update_neurons.assert_called_once_with([new_neuron])
    assert axons["new_hotkey"] == "3.3.3.3"

    mock_debug.assert_any_call(
        "🗑️ # Neurons removed: 1",
        prefix=observer.settings.logging_name,
    )


@pytest.mark.asyncio
@patch("bittensor.utils.btlogging.logging.debug")
async def test_resync_removes_stale_hotkey(mock_debug, observer):
    fake_proto = MagicMock()
    fake_proto.uid = 1
    fake_proto.axon_info.ip = "3.3.3.3"
    fake_proto.hotkey = "new_hotkey"

    old_neuron = scmm.Neuron(uid=-1, ip="3.3.3.3", hotkey="old_hotkey", country="US")
    new_neuron = scmm.Neuron(uid=1, ip="3.3.3.3", hotkey="new_hotkey", country=None)

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={old_neuron.hotkey: old_neuron}
    )
    observer.database.update_neurons = AsyncMock()
    observer.database.remove_neurons = AsyncMock()

    with (
        patch(
            "subvortex.core.model.neuron.neuron.Neuron.from_proto",
            return_value=new_neuron,
        ),
        patch("subvortex.core.country.country.get_country", return_value="US"),
    ):
        axons, _ = await observer._resync()

    observer.database.remove_neurons.assert_called_once_with([old_neuron])
    observer.database.update_neurons.assert_called_once_with([new_neuron])
    assert axons["new_hotkey"] == "3.3.3.3"

    mock_debug.assert_any_call(
        "🗑️ # Stale neurons removed: 1",
        prefix=observer.settings.logging_name,
    )


@pytest.mark.asyncio
async def test_resync_triggers_on_missing_country(observer):
    """Test that a neuron with a missing country triggers has_missing_country=True."""
    fake_proto = MagicMock()
    fake_proto.uid = 101
    fake_proto.axon_info.ip = "4.4.4.4"
    fake_proto.hotkey = "missing_country_hotkey"

    # Simulate stored neuron with same UID but no country
    old_neuron = scmm.Neuron(
        uid=101, ip="4.4.4.4", hotkey="missing_country_hotkey", country=None
    )
    new_neuron = scmm.Neuron(
        uid=101, ip="4.4.4.4", hotkey="missing_country_hotkey", country="BR"
    )

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={old_neuron.hotkey: old_neuron}
    )
    observer.database.update_neurons = AsyncMock()

    with patch(
        "subvortex.core.model.neuron.neuron.Neuron.from_proto",
        return_value=new_neuron,
    ), patch(
        "subvortex.core.country.country.get_country",
        return_value=new_neuron.country,
    ):
        axons, has_missing_country = await observer._resync()

    assert has_missing_country is False
    observer.database.remove_neurons.assert_not_called()
    observer.database.update_neurons.assert_called_once_with([new_neuron])
    assert axons["missing_country_hotkey"] == "4.4.4.4"


@pytest.mark.asyncio
async def test_resync_triggers_on_keep_missing_country(observer):
    """Test that a neuron with a missing country triggers has_missing_country=True."""
    fake_proto = MagicMock()
    fake_proto.uid = 101
    fake_proto.axon_info.ip = "4.4.4.4"
    fake_proto.hotkey = "missing_country_hotkey"

    # Simulate stored neuron with same UID but no country
    old_neuron = scmm.Neuron(
        uid=101, ip="4.4.4.4", hotkey="missing_country_hotkey", country=None
    )
    new_neuron = scmm.Neuron(
        uid=101, ip="4.4.4.4", hotkey="missing_country_hotkey", country=None
    )

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(
        return_value={old_neuron.hotkey: old_neuron}
    )
    observer.database.update_neurons = AsyncMock()

    with patch(
        "subvortex.core.model.neuron.neuron.Neuron.from_proto",
        return_value=new_neuron,
    ), patch(
        "subvortex.core.country.country.get_country",
        return_value=new_neuron.country,
    ):
        axons, has_missing_country = await observer._resync()

    assert has_missing_country is True
    observer.database.remove_neurons.assert_not_called()
    observer.database.update_neurons.assert_called_once_with([new_neuron])
    assert axons["missing_country_hotkey"] == "4.4.4.4"


@pytest.mark.asyncio
async def test_ip_change_same_hotkey_no_delete(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 1
    fake_proto.axon_info.ip = "10.10.10.10"
    fake_proto.hotkey = "same_hotkey"

    stored = scmm.Neuron(uid=1, ip="1.1.1.1", hotkey="same_hotkey", country="US")
    updated = scmm.Neuron(uid=1, ip="10.10.10.10", hotkey="same_hotkey", country="FR")

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(return_value={"same_hotkey": stored})
    observer.database.update_neurons = AsyncMock()
    observer.database.remove_neurons = AsyncMock()

    with patch(
        "subvortex.core.model.neuron.neuron.Neuron.from_proto",
        return_value=updated,
    ), patch("subvortex.core.country.country.get_country", return_value="FR"):
        axons, _ = await observer._resync()

    observer.database.remove_neurons.assert_not_called()
    observer.database.update_neurons.assert_called_once_with([updated])


@pytest.mark.asyncio
async def test_resync_removes_stale_neuron(observer):
    fake_proto = MagicMock()
    fake_proto.uid = 2
    fake_proto.axon_info.ip = "2.2.2.2"
    fake_proto.hotkey = "newer_hotkey"

    stored = scmm.Neuron(
        uid=99, ip="99.99.99.99", hotkey="old_stale_hotkey", country="US"
    )
    new = scmm.Neuron(uid=2, ip="2.2.2.2", hotkey="newer_hotkey", country="FR")

    observer.metagraph = AsyncMock()
    observer.metagraph.neurons = [fake_proto]
    observer.database.get_neurons = AsyncMock(return_value={stored.hotkey: stored})
    observer.database.remove_neurons = AsyncMock()
    observer.database.update_neurons = AsyncMock()

    with patch(
        "subvortex.core.model.neuron.neuron.Neuron.from_proto",
        return_value=new,
    ), patch("subvortex.core.country.country.get_country", return_value="FR"):
        axons, _ = await observer._resync()

    observer.database.remove_neurons.assert_called_once_with([stored])
    observer.database.update_neurons.assert_called_once_with([new])
