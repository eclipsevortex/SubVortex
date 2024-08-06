import requests
import subprocess
import bittensor as bt
from os import path
from subnet.shared.utils import get_version


here = path.abspath(path.dirname(__file__))


class Github:
    def __init__(self, repo_owner="eclipsevortex", repo_name="SubVortex"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.latest_version = None

    def get_version(self) -> str:
        return get_version()

    def get_latest_version(self) -> str:
        """
        Get the latest release on github
        Return the cached value if any errors
        """
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            response = requests.get(url)
            if response.status_code != 200:
                return self.latest_version

            latest_version = response.json()["tag_name"]
            self.latest_version = latest_version[1:]
            return self.latest_version
        except Exception:
            return self.latest_version

    def get_branch(self, branch_name="main"):
        """
        Get the expected branch
        """
        # Stash if there is any local changes just in case
        subprocess.run(["git", "stash"], check=True)

        # Checkout branch
        subprocess.run(["git", "checkout", "-B", branch_name], check=True)

        # Set tracking
        subprocess.run(
            ["git", "branch", f"--set-upstream-to=origin/{branch_name}", branch_name],
            check=True,
        )

        # Pull branch
        subprocess.run(["git", "reset", "--hard", f"origin/{branch_name}"], check=True)

        # Stash if there is any local changes just in case
        subprocess.run(["git", "stash"], check=True)

        bt.logging.info(f"Successfully pulled source code for branch '{branch_name}'.")

    def get_tag(self, tag):
        """
        Get the expected tag
        """
        # Stash if there is any local changes just in case
        subprocess.run(["git", "stash"], check=True)

        # Fetch tags
        subprocess.run(["git", "fetch", "--tags", "--force"], check=True)
        bt.logging.info(f"Fetch tags.")

        # Checkout tags
        subprocess.run(["git", "checkout", f"tags/{tag}"], check=True)
        bt.logging.info(f"Successfully pulled source code for tag '{tag}'.")
