import unittest
from unittest.mock import patch

from subnet.version.utils import get_migrations


class TestUtilVersionControl(unittest.IsolatedAsyncioTestCase):
    @patch("os.listdir")
    async def test_no_migration_available_should_return_an_empty_list(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = []

        # Act
        result = get_migrations()

        # Assert
        assert 0 == len(result)

    @patch("os.listdir")
    async def test_migration_available_should_return_a_list_in_the_right_order(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = [
            "migration-2.1.0.py",
            "migration-2.0.0.py",
            "migration-2.1.1.py",
        ]

        # Act
        result = get_migrations()

        # Assert
        assert 3 == len(result)
        assert (211, "2.1.1", "migration-2.1.1.py") == result[0]
        assert (210, "2.1.0", "migration-2.1.0.py") == result[1]
        assert (200, "2.0.0", "migration-2.0.0.py") == result[2]

    @patch("os.listdir")
    async def test_migration_available_when_few_does_match_the_expected_pattern_should_return_a_list_without_these_wrong_formatted_files(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = [
            "migration2.1.1.py",
            "migrations-2.0.0.py",
            "migration-210.py",
        ]

        # Act
        result = get_migrations()

        # Assert
        assert 0 == len(result)
