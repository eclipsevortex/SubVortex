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

from subnet.version.github_controller import Github


class TestGithubController(unittest.IsolatedAsyncioTestCase):
    @patch("requests.get")
    @patch("codecs.open")
    def test_request_latest_successful_should_return_the_latest_version(
        self, mock_open, mock_request
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = ""

        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"tag_name": "v2.2.3"}

        github = Github()

        # Act
        result = github.get_latest_version()

        # Assert
        assert "2.2.3" == result

    @patch("requests.get")
    @patch("codecs.open")
    def test_request_latest_failed_and_no_cached_version_exist_should_return_none(
        self, mock_open, mock_request
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = ""

        mock_request.return_value.status_code = 300
        mock_request.return_value.json.return_value = {"tag_name": "v2.2.3"}

        github = Github()

        # Act
        result = github.get_latest_version()

        # Assert
        assert None == result

    @patch("requests.get")
    @patch("codecs.open")
    def test_request_latest_failed_and_a_cached_version_exist_should_return_the_cached_version(
        self, mock_open, mock_request
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = ""

        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"tag_name": "v2.2.3"}

        github = Github()

        # Act
        result1 = github.get_latest_version()

        # Assert
        assert "2.2.3" == result1

        # Arrange
        mock_request.return_value.status_code = 300
        mock_request.return_value.json.return_value = {"tag_name": "v2.2.4"}

        # Act
        result2 = github.get_latest_version()

        assert "2.2.3" == result2

    @patch("requests.get")
    @patch("codecs.open")
    def test_request_latest_throw_exception_and_a_cached_version_exist_should_return_the_cached_version(
        self, mock_open, mock_request
    ):
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = ""

        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"tag_name": "v2.2.3"}

        github = Github()

        # Act
        result1 = github.get_latest_version()

        # Assert
        assert "2.2.3" == result1

        # Arrange
        mock_request.return_value.json.return_value = ValueError("Simulated error")

        # Act
        result2 = github.get_latest_version()

        assert "2.2.3" == result2
