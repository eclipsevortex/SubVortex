# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

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
import unittest
from unittest.mock import patch

from subnet.version.utils import get_migrations


class TestUtilVersionControl(unittest.IsolatedAsyncioTestCase):
    @patch("os.listdir")
    async def test_forward_order_with_order_with_no_migration_available_should_return_an_empty_list(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = []

        # Act
        result = get_migrations()

        # Assert
        assert 0 == len(result)

    @patch("os.listdir")
    async def test_forward_order_with_migration_available_should_return_a_list_in_the_right_order(
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
        assert (200, "2.0.0", "migration-2.0.0.py") == result[0]
        assert (210, "2.1.0", "migration-2.1.0.py") == result[1]
        assert (211, "2.1.1", "migration-2.1.1.py") == result[2]

    @patch("os.listdir")
    async def test_forward_order_with_migration_available_and_filter_applied_should_return_a_list_in_the_right_order(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = [
            "migration-2.1.0.py",
            "migration-2.0.0.py",
            "migration-2.1.1.py",
        ]

        # Act
        result = get_migrations(filter_lambda=lambda x: x[0] > 200 and x[0] <= 211)

        # Assert
        assert 2 == len(result)
        assert (210, "2.1.0", "migration-2.1.0.py") == result[0]
        assert (211, "2.1.1", "migration-2.1.1.py") == result[1]

    @patch("os.listdir")
    async def test_forward_order_with_migration_available_when_few_does_match_the_expected_pattern_should_return_a_list_without_these_wrong_formatted_files(
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

    @patch("os.listdir")
    async def test_reverse_order_with_no_migration_available_should_return_an_empty_list(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = []

        # Act
        result = get_migrations(reverse=True)

        # Assert
        assert 0 == len(result)

    @patch("os.listdir")
    async def test_reverse_order_with_migration_available_should_return_a_list_in_the_right_order(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = [
            "migration-2.1.0.py",
            "migration-2.0.0.py",
            "migration-2.1.1.py",
        ]

        # Act
        result = get_migrations(reverse=True)

        # Assert
        assert 3 == len(result)
        assert (211, "2.1.1", "migration-2.1.1.py") == result[0]
        assert (210, "2.1.0", "migration-2.1.0.py") == result[1]
        assert (200, "2.0.0", "migration-2.0.0.py") == result[2]

    @patch("os.listdir")
    async def test_reverse_order_with_migration_available_and_filter_applied_should_return_a_list_in_the_right_order(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = [
            "migration-2.1.0.py",
            "migration-2.0.0.py",
            "migration-2.1.1.py",
        ]

        # Act
        result = get_migrations(
            reverse=True, filter_lambda=lambda x: x[0] > 200 and x[0] <= 211
        )

        # Assert
        assert 2 == len(result)
        assert (211, "2.1.1", "migration-2.1.1.py") == result[0]
        assert (210, "2.1.0", "migration-2.1.0.py") == result[1]

    @patch("os.listdir")
    async def test_reverse_order_with_migration_available_when_few_does_match_the_expected_pattern_should_return_a_list_without_these_wrong_formatted_files(
        self, mock_listdir
    ):
        # Arrange
        mock_listdir.return_value = [
            "migration2.1.1.py",
            "migrations-2.0.0.py",
            "migration-210.py",
        ]

        # Act
        result = get_migrations(reverse=True)

        # Assert
        assert 0 == len(result)
