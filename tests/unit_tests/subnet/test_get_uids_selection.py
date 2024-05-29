from subnet.validator.selection import select_uids

from tests.unit_tests.mocks import mock_miners
from tests.unit_tests.utils.utils import count_non_unique, count_unique

# List of 18 miners from uid 0 to 17
miners = sorted(
    [
        mock_miners.miner_default,
        mock_miners.miner_gb_1,
        mock_miners.miner_gb_2,
        mock_miners.miner_not_verified_1,
        mock_miners.miner_not_verified_2,
        mock_miners.miner_not_verified_3,
        mock_miners.miner_not_verified_and_ip_conflicts_1,
        mock_miners.miner_not_verified_and_ip_conflicts_2,
        mock_miners.miner_with_worst_latency,
        mock_miners.miner_with_in_between_latency,
        mock_miners.miner_with_best_latency,
        mock_miners.miner_unique_localisation,
        mock_miners.miner_verified,
        mock_miners.miner_with_30_percent_to_the_best_in_between_latency,
        mock_miners.miner_with_30_percent_to_the_worst_in_between_latency,
        mock_miners.miner_with_ip_conflicts_1,
        mock_miners.miner_with_ip_conflicts_2,
        mock_miners.miner_not_verified_and_ip_conflicts_3,
    ],
    key=lambda x: x.uid,
)


def test_one_active_validator_should_select_all_miners_fairly():
    # Step 1
    # Arrange
    expected = [10, 11, 12, 13]

    # Act
    selection = select_uids(
        20,
        1,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c5",
        miners,
        [20],
        k=4,
    )

    # Assert
    selection_sorted = sorted(selection)
    assert 4 == len(selection_sorted)
    assert True == all(x in expected for x in selection_sorted)

    # Step 2
    # Arrange
    expected = [6, 7, 8, 9]

    # Act
    selection = select_uids(
        20,
        2,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c6",
        miners,
        [20],
        k=4,
    )

    # Assert
    selection_sorted = sorted(selection)
    assert 4 == len(selection_sorted)
    assert True == all(x in expected for x in selection_sorted)

    # Step 3
    # Arrange
    expected = [2, 3, 4, 5]

    # Act
    selection = select_uids(
        20,
        3,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c7",
        miners,
        [20],
        k=4,
    )

    # Assert
    selection_sorted = sorted(selection)
    assert 4 == len(selection_sorted)
    assert True == all(x in expected for x in selection_sorted)

    # Step 4
    # Arrange
    expected = [0, 1, 16, 17]

    # Act
    selection = select_uids(
        20,
        4,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c8",
        miners,
        [20],
        k=4,
    )

    # Assert
    selection_sorted = sorted(selection)
    assert 4 == len(selection_sorted)
    assert True == all(x in expected for x in selection_sorted)

    # Step 5
    # Arrange
    expected = [12, 13, 14, 15]

    # Act
    selection = select_uids(
        20,
        5,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c9",
        miners,
        [20],
        k=4,
    )

    # Assert
    selection_sorted = sorted(selection)
    assert 4 == len(selection_sorted)
    assert True == all(x in expected for x in selection_sorted)


def test_multiple_active_validators_should_select_all_miners_fairly():
    selection = []

    # Step 1
    # Arrange

    # Act
    val_selection_1 = select_uids(
        20,
        1,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c5",
        miners,
        [20, 21],
        k=4,
    )
    val_selection_2 = select_uids(
        21,
        20270179,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c5",
        miners,
        [20, 21],
        k=4,
    )

    # Assert
    selection = selection + val_selection_1 + val_selection_2
    assert 4 == len(val_selection_1)
    assert 4 == len(val_selection_2)
    assert True == all(x not in val_selection_2 for x in val_selection_1)
    assert 8 == count_unique(selection)
    assert 0 == count_non_unique(selection)

    # Step 2
    # Arrange

    # Act
    val_selection_1 = select_uids(
        20,
        2,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c6",
        miners,
        [20, 21],
        k=4,
    )
    val_selection_2 = select_uids(
        21,
        20270180,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c6",
        miners,
        [20, 21],
        k=4,
    )

    # Assert
    selection = selection + val_selection_1 + val_selection_2
    assert 4 == len(val_selection_1)
    assert 4 == len(val_selection_2)
    assert True == all(x not in val_selection_2 for x in val_selection_1)
    assert 16 == count_unique(selection)
    assert 0 == count_non_unique(selection)

    # Step 3
    # Arrange

    # Act
    val_selection_1 = select_uids(
        20,
        3,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c7",
        miners,
        [20, 21],
        k=4,
    )
    val_selection_2 = select_uids(
        21,
        20270181,
        "0x1c1ad91722bfc017da9087f019f5e8c5265b7aacf9fb813d15445eaada98d1c7",
        miners,
        [20, 21],
        k=4,
    )

    # Assert
    selection = selection + val_selection_1 + val_selection_2
    assert 4 == len(val_selection_1)
    assert 4 == len(val_selection_2)
    assert True == all(x not in val_selection_2 for x in val_selection_1)
    assert 24 == len(selection)
    assert 18 == count_unique(selection)
    assert 6 == count_non_unique(selection)
