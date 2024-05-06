import os
import sys
import bittensor as bt

from subnet.shared.version import BaseVersionControl


class VersionControl(BaseVersionControl):
    def restart(self):
        bt.logging.info(f"Restarting miner...")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def upgrade_miner(self):
        current_version = None

        try:
            # Get the remote version
            remote_version = self.github.get_latest_version()
            bt.logging.debug(f"[Subnet] Remote version: {remote_version}")

            # Get the local version
            current_version = self.github.get_version()
            bt.logging.debug(f"[Subnet] Local version: {current_version}")

            # Check if the subnet has to be upgraded
            if current_version == remote_version:
                bt.logging.success(f"[Subnet] Already using {current_version}")
                return

            self.must_restart = True

            current_version_num = int(current_version.replace(".", ""))
            remote_version_num = int(remote_version.replace(".", ""))

            if remote_version_num > current_version_num:
                success = self.upgrade_subnet(remote_version)
            else:
                success = self.downgrade_subnet(remote_version)

            if not success:
                self.downgrade_subnet(current_version)
        except Exception as err:
            bt.logging.error(f"[Subnet] Upgrade failed: {err}")
            bt.logging.info(f"[Subnet] Rolling back to {current_version}...")
            self.downgrade_subnet(current_version)

    def upgrade(self):
        try:
            # Flag to stop miner activity
            self.upgrading = True

            # Upgrade subnet
            self.upgrade_miner()

            return self.must_restart
        except Exception as ex:
            bt.logging.error(f"Could not upgrade the miner: {ex}")
        finally:
            # Unflag to resume miner activity
            self.upgrading = False
            self.must_restart = False

        return True
