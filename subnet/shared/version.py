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
import threading
import bittensor.utils.btlogging as btul

from subnet.version.github_controller import Github
from subnet.version.interpreter_controller import Interpreter


class BaseVersionControl:
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.github = Github()
        self.interpreter = Interpreter()
        self._upgrading = False
        self.must_restart = False

    @property
    def upgrading(self):
        with self._lock:
            return self._upgrading

    @upgrading.setter
    def upgrading(self, value):
        with self._lock:
            self._upgrading = value

    def upgrade_subnet(self, version: str = None, tag: str = None, branch: str = None):
        """
        Upgrade the subnet with the requested version or the latest one
        Version has to follow the format major.minor.patch
        """
        try:
            btul.logging.info("[Subnet] Upgrading...")

            if branch is not None:
                # Pull the branch
                self.github.get_branch(branch)
            else:
                # Pull the tag
                github_tag = f"v{version or tag}"
                self.github.get_tag(github_tag)

            # Install dependencies
            self.interpreter.install_dependencies()

            if branch:
                btul.logging.success(f"[Subnet] Upgrade to branch {branch} successful")
            elif tag:
                btul.logging.success(f"[Subnet] Upgrade to tag {tag} successful")
            else:
                btul.logging.success(f"[Subnet] Upgrade to {version} successful")

            return True
        except Exception as err:
            btul.logging.error(f"[Subnet] Failed to upgrade the subnet: {err}")

        return False

    def downgrade_subnet(self, version: str):
        """
        Downgrade the subnet with the requested version
        Version has to follow the format major.minor.patch
        """
        try:
            # Pull the branch
            self.github.get_tag(f"v{version}")

            # Install dependencies
            self.interpreter.install_dependencies()

            btul.logging.success(f"[Subnet] Downgrade to {version} successful")

            return True
        except Exception as err:
            btul.logging.error(f"[Subnet] Failed to upgrade the subnet: {err}")

        return False
