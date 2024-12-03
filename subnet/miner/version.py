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
import os
import sys
import subprocess
from os import path
import bittensor.utils.btlogging as btul

from subnet.shared.version import BaseVersionControl


here = path.abspath(path.dirname(__file__))


class VersionControl(BaseVersionControl):
    def restart(self):
        btul.logging.info(f"Restarting miner...")
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
                btul.logging.success(f"[OS] Upgrade successful")
            else:
                btul.logging.warning(f"[OS] Upgrade failed {result.stderr}")
        except subprocess.CalledProcessError as err:
            btul.logging.error(f"[OS] Upgrade failed: {err}")

    def upgrade_miner(self, tag=None, branch=None):
        current_version = None

        try:
            # Get the remote version
            remote_version = self.github.get_latest_version()
            btul.logging.debug(f"[Subnet] Remote version: {remote_version}")

            # Get the local version
            current_version = self.github.get_version()
            btul.logging.debug(f"[Subnet] Local version: {current_version}")

            # True if there is a custom tag or branch, false otherwise
            is_custom_version = tag is not None or branch is not None

            # Check if the subnet has to be upgraded
            if not is_custom_version and current_version == remote_version:
                btul.logging.success(f"[Subnet] Already using {current_version}")
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
            btul.logging.error(f"[Subnet] Upgrade failed: {err}")
            btul.logging.info(f"[Subnet] Rolling back to {current_version}...")
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
            btul.logging.error(f"Could not upgrade the miner: {ex}")
        finally:
            # Unflag to resume miner activity
            self.upgrading = False
            self.must_restart = False

        return True
