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
from os import path
from unittest.mock import patch, MagicMock, call

from tests.unit_tests.test_case import TestCase
from tests.unit_tests.mocks.mock_interpreter import install_depdencies_side_effect

from subnet.miner.version import VersionControl

here = path.abspath("subnet/miner")


class TestMinerVersionControl(TestCase):
    def assert_update_os_packages_called_with(self, mock_subprocess):
        script_path = path.join(here, "../../scripts/os/os_setup.sh")
        mock_subprocess.assert_called_with(
            ["bash", script_path, "-t", "miner"],
            check=True,
            text=True,
            capture_output=True,
        )

    @patch("subprocess.run")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    def test_no_new_version_available_when_upgradring_should_do_nothing(
        self, mock_github, mock_interpreter, mock_subprocess
    ):
        # Arrange
        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        vc = VersionControl()

        # Act
        must_restart = vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_not_called()
        mock_interpreter_class.install_dependencies.assert_not_called()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert False == must_restart

    @patch("subprocess.run")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    def test_new_higher_version_available_when_upgradring_should_upgrade_the_miner(
        self, mock_github, mock_interpreter, mock_subprocess
    ):
        # Arrange
        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.1.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        vc = VersionControl()

        # Act
        must_restart = vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_called_with("v2.1.0")
        mock_interpreter_class.install_dependencies.assert_called_once()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    def test_upgrading_to_a_new_higher_version_when_failing_should_downgrade_to_the_old_current_version(
        self, mock_github, mock_interpreter, mock_subprocess
    ):
        # Arrange
        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.1.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        install_depdencies_side_effect.called = False
        mock_interpreter_class.install_dependencies.side_effect = (
            install_depdencies_side_effect
        )
        mock_interpreter.return_value = mock_interpreter_class

        vc = VersionControl()

        # Act
        must_restart = vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_has_calls([call("v2.1.0"), call("v2.0.0")])
        mock_interpreter_class.install_dependencies.assert_has_calls([call(), call()])
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    def test_current_version_removed_when_upgradring_should_downgrade_the_miner(
        self, mock_github, mock_interpreter, mock_subprocess
    ):
        # Arrange
        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.1.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        vc = VersionControl()

        # Act
        must_restart = vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_called_with("v2.0.0")
        mock_interpreter_class.install_dependencies.assert_called_once()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart
