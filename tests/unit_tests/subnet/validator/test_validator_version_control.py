import aioredis
import unittest
from os import path
from unittest.mock import patch, MagicMock, call, AsyncMock

from tests.unit_tests.mocks.mock_interpreter import install_depdencies_side_effect
from tests.unit_tests.mocks.mock_redis import rollout_side_effect

from subnet.validator.version import VersionControl

here = path.abspath("subnet/validator")


class TestValidatorVersionControl(unittest.IsolatedAsyncioTestCase):
    def assert_update_os_packages_called_with(self, mock_subprocess):
        script_path = path.join(here, "../../scripts/os/os_setup.sh")
        mock_subprocess.assert_called_with(
            ["bash", script_path, "-t", "validator"],
            check=True,
            text=True,
            capture_output=True,
        )

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_no_new_version_available_when_upgradring_should_do_nothing(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.database = AsyncMock(aioredis.Redis)
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.0.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_not_called()
        mock_interpreter_class.install_dependencies.assert_not_called()
        mock_create_dump.assert_not_called()
        mock_redis_class.rollout.assert_not_called()
        mock_redis_class.rollback.assert_not_called()
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_called_once()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert False == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_new_higher_validator_version_available_when_upgradring_should_upgrade_the_validator(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.database = AsyncMock(aioredis.Redis)
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.0.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.1.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_called_with("v2.1.0")
        mock_interpreter_class.install_dependencies.assert_called_once()
        mock_redis_class.rollout.assert_not_called()
        mock_redis_class.rollback.assert_not_called()
        mock_create_dump.assert_not_called()
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_called_once()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_new_validator_higher_version_available_when_failing_upgrading_should_rollback_the_validator_to_keep_the_current_version(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.database = AsyncMock(aioredis.Redis)
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.0.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis.return_value = mock_redis_class

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

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_has_calls([call("v2.1.0"), call("v2.0.0")])
        mock_interpreter_class.install_dependencies.assert_has_calls([call(), call()])
        mock_redis_class.rollout.assert_not_called()
        mock_redis_class.rollback.assert_not_called()
        mock_create_dump.assert_not_called()
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_called_once()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_current_validator_version_removed_when_upgradring_should_downgrade_the_validator(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.database = AsyncMock(aioredis.Redis)
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.0.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.1.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_called_with("v2.0.0")
        mock_interpreter_class.install_dependencies.assert_called_once()
        mock_redis_class.rollout.assert_not_called()
        mock_redis_class.rollback.assert_not_called()
        mock_create_dump.assert_not_called()
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_called_once()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_new_higher_redis_version_available_when_upgradring_should_upgrade_redis(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.1.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis_class.rollout = AsyncMock()
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        mock_create_dump.return_value = AsyncMock()

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_not_called()
        mock_interpreter_class.install_dependencies.assert_not_called()
        mock_redis_class.rollout.assert_called_once_with("2.0.0", "2.1.0")
        mock_redis_class.rollback.assert_not_called()
        mock_create_dump.assert_called_once_with(
            "/etc/redis/redis-dump-2.0.0", mock_redis_class.database
        )
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_has_calls([call(), call()])
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_new_higher_redis_version_available_when_failing_upgrading_should_rollback_redis_to_keep_the_current_version(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.1.0"
        mock_redis_class.dump_path = "/etc/redis"
        rollout_side_effect.called = False
        mock_redis_class.rollout.side_effect = rollout_side_effect
        mock_redis_class.rollback = AsyncMock()
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        mock_create_dump.return_value = AsyncMock()

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_not_called()
        mock_interpreter_class.install_dependencies.assert_not_called()
        mock_redis_class.rollout.assert_called_once_with("2.0.0", "2.1.0")
        mock_redis_class.rollback.assert_called_once_with("2.1.0", "2.0.0")
        mock_create_dump.assert_called_once_with(
            "/etc/redis/redis-dump-2.0.0", mock_redis_class.database
        )
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_has_calls([call(), call()])
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_new_higher_redis_version_available_when_failing_upgrading_and_failling_rollbacking_should_restore_the_dump_to_keep_the_current_version(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.1.0"
        mock_redis_class.dump_path = "/etc/redis"
        rollout_side_effect.called = False
        mock_redis_class.rollout.side_effect = rollout_side_effect
        mock_redis_class.rollback = AsyncMock(return_value=False)
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        mock_create_dump.return_value = AsyncMock()

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_not_called()
        mock_interpreter_class.install_dependencies.assert_not_called()
        mock_redis_class.rollout.assert_called_once_with("2.0.0", "2.1.0")
        mock_redis_class.rollback.assert_called_once_with("2.1.0", "2.0.0")
        mock_create_dump.assert_called_once_with(
            "/etc/redis/redis-dump-2.0.0", mock_redis_class.database
        )
        mock_restore_dump.assert_called_once_with(
            "/etc/redis/redis-dump-2.0.0", mock_redis_class.database
        )
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_has_calls([call(), call()])
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_current_redis_version_removed_when_upgradring_should_downgrade_redis(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.database = AsyncMock(aioredis.Redis)
        mock_redis_class.get_version = AsyncMock(return_value="2.1.0")
        mock_redis_class.get_latest_version.return_value = "2.0.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis_class.rollout = AsyncMock()
        mock_redis_class.rollback = AsyncMock()
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.0.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        mock_create_dump.return_value = AsyncMock()

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_not_called()
        mock_interpreter_class.install_dependencies.assert_not_called()
        mock_redis_class.rollout.assert_not_called()
        mock_redis_class.rollback.assert_called_once_with("2.1.0", "2.0.0")
        mock_create_dump.assert_called_once_with(
            "/etc/redis/redis-dump-2.1.0", mock_redis_class.database
        )
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_called_once()
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_new_higher_miner_and_redis_version_available_when_upgradring_should_upgrade_both(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.1.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis_class.rollout = AsyncMock()
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.1.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        mock_create_dump.return_value = AsyncMock()

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_called_with("v2.1.0")
        mock_interpreter_class.install_dependencies.assert_called_once()
        mock_redis_class.rollout.assert_called_once_with("2.0.0", "2.1.0")
        mock_create_dump.assert_called_once_with(
            "/etc/redis/redis-dump-2.0.0", mock_redis_class.database
        )
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_has_calls([call(), call()])
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart

    @patch("subprocess.run")
    @patch("subnet.validator.version.remove_dump_migrations")
    @patch("subnet.validator.version.create_dump_migrations")
    @patch("subnet.validator.version.restore_dump")
    @patch("subnet.validator.version.create_dump")
    @patch("subnet.shared.version.Interpreter")
    @patch("subnet.shared.version.Github")
    @patch("subnet.validator.version.Redis")
    async def test_new_higher_miner_and_redis_version_available_when_validator_uprade_succeed_and_redis_upgrade_failed_should_rollback_the_validator_version(
        self,
        mock_redis,
        mock_github,
        mock_interpreter,
        mock_create_dump,
        mock_restore_dump,
        more_create_dump_migrations,
        more_remove_dump_migrations,
        mock_subprocess,
    ):
        # Arrange
        mock_redis_class = MagicMock()
        mock_redis_class.get_version = AsyncMock(return_value="2.0.0")
        mock_redis_class.get_latest_version.return_value = "2.1.0"
        mock_redis_class.dump_path = "/etc/redis"
        mock_redis_class.rollout = AsyncMock()
        rollout_side_effect.called = False
        mock_redis_class.rollout.side_effect = rollout_side_effect
        mock_redis_class.rollback = AsyncMock()
        mock_redis.return_value = mock_redis_class

        mock_github_class = MagicMock()
        mock_github_class.get_version.return_value = "2.0.0"
        mock_github_class.get_latest_version.return_value = "2.1.0"
        mock_github.return_value = mock_github_class

        mock_interpreter_class = MagicMock()
        mock_interpreter.return_value = mock_interpreter_class

        mock_create_dump.return_value = AsyncMock()

        vc = VersionControl(mock_redis.database, mock_redis_class.dump_path)

        # Act
        must_restart = await vc.upgrade()

        # Assert
        mock_github_class.get_tag.assert_has_calls([call("v2.1.0"), call("v2.0.0")])
        mock_interpreter_class.install_dependencies.assert_has_calls([call(), call()])
        mock_redis_class.rollout.assert_called_once_with("2.0.0", "2.1.0")
        mock_redis_class.rollback.assert_called_once_with("2.1.0", "2.0.0")
        mock_create_dump.assert_called_once_with(
            "/etc/redis/redis-dump-2.0.0", mock_redis_class.database
        )
        mock_restore_dump.assert_not_called()
        more_create_dump_migrations.assert_called_once()
        more_remove_dump_migrations.assert_has_calls([call(), call()])
        self.assert_update_os_packages_called_with(mock_subprocess)
        assert True == must_restart
