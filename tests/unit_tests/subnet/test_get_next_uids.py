import pytest

from subnet.constants import DEFAULT_CHUNK_SIZE
from subnet.validator.utils import get_next_uids
from tests.unit_tests.mocks import mock_redis
from tests.unit_tests.utils.utils import generate_random_ip
from tests.unit_tests.utils.utils import count_non_unique, count_unique


@pytest.mark.asyncio
async def test_select_uids_fairly(
    validator,
):
    # Step 1
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    val_hotkey = validator.metagraph.hotkeys[validator.uid]
    validator.database = mock_redis.mock_get_selection(val_hotkey)

    # Act
    selection_1 = await get_next_uids(validator, val_hotkey, k=DEFAULT_CHUNK_SIZE)

    # Assert
    assert DEFAULT_CHUNK_SIZE == len(selection_1)
    assert DEFAULT_CHUNK_SIZE == count_unique(selection_1)

    # Step 2
    # Arrange
    val_hotkey = validator.metagraph.hotkeys[validator.uid]
    validator.database = mock_redis.mock_get_selection(val_hotkey, selection_1)

    # Act
    selection_2 = await get_next_uids(validator, val_hotkey, k=DEFAULT_CHUNK_SIZE)

    # Assert
    assert DEFAULT_CHUNK_SIZE == len(selection_2)
    assert DEFAULT_CHUNK_SIZE == count_unique(selection_2)
    assert 3 == count_non_unique(selection_1 + selection_2)
