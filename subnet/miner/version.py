import os
import sys
import subprocess
from os import path
import bittensor as bt

from subnet.shared.version import BaseVersionControl


here = path.abspath(path.dirname(__file__))


class VersionControl(BaseVersionControl):
    def restart(self):
        bt.logging.info(f"Restarting miner...")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def update_os_packages(self):
        try:
            script_path = path.join(here, "../../scripts/os/os_setup.sh")
            result = subprocess.run(
                ["bash", script_path, "-t", "miner"],
                check=True,
                text=True,
                capture_output=True,
            )

            if result.returncode == 0:
                bt.logging.success(f"[OS] Upgrade successful")
            else:
                bt.logging.warning(f"[OS] Upgrade failed {result.stderr}")
        except subprocess.CalledProcessError as err:
            bt.logging.error(f"[OS] Upgrade failed: {err}")

    def upgrade_miner(self, tag=None, branch=None):
        current_version = None

        try:
            # Get the remote version
            remote_version = self.github.get_latest_version()
            bt.logging.debug(f"[Subnet] Remote version: {remote_version}")

            # Get the local version
            current_version = self.github.get_version()
            bt.logging.debug(f"[Subnet] Local version: {current_version}")

            # True if there is a custom tag or branch, false otherwise
            is_custom_version = tag is not None or branch is not None

            # Check if the subnet has to be upgraded
            if not is_custom_version and current_version == remote_version:
                bt.logging.success(f"[Subnet] Already using {current_version}")
                return

            self.must_restart = True

            current_version_num = int(current_version.replace(".", ""))
            remote_version_num = int(remote_version.replace(".", ""))

            if is_custom_version:
                success = self.upgrade_subnet(tag=tag, branch=branch)
            elif remote_version_num > current_version_num:
                success = self.upgrade_subnet(version=remote_version)
            else:
                success = self.downgrade_subnet(version=remote_version)

            if not success:
                self.downgrade_subnet(current_version)
        except Exception as err:
            bt.logging.error(f"[Subnet] Upgrade failed: {err}")
            bt.logging.info(f"[Subnet] Rolling back to {current_version}...")
            self.downgrade_subnet(current_version)

    def upgrade(self, tag=None, branch=None):
        try:
            # Flag to stop miner activity
            self.upgrading = True

            # Install os packages
            self.update_os_packages()

            # Upgrade subnet
            self.upgrade_miner(tag=tag, branch=branch)

            return self.must_restart
        except Exception as ex:
            bt.logging.error(f"Could not upgrade the miner: {ex}")
        finally:
            # Unflag to resume miner activity
            self.upgrading = False
            self.must_restart = False

        return True
