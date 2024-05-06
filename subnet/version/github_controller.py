import re
import os
import codecs
import requests
import subprocess
import bittensor as bt
from os import path


here = path.abspath(path.dirname(__file__))


class Github:
    def __init__(self, repo_owner="eclipsevortex", repo_name="SubVortexVC"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name

    def get_version(self) -> str:
        with codecs.open(
            os.path.join(here, "../__init__.py"), encoding="utf-8"
        ) as init_file:
            version_match = re.search(
                r"^__version__ = ['\"]([^'\"]*)['\"]", init_file.read(), re.M
            )
            version_string = version_match.group(1)
            return version_string

    def get_latest_version(self) -> str:
        """
        Get the latest release on github
        """
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        response = requests.get(url)
        if response.status_code != 200:
            return None

        latest_version = response.json()["tag_name"]
        return latest_version[1:]

    def get_branch(self, tag="latest"):
        """
        Get the expected branch
        """
        if tag == "latest":
            subprocess.run(["git", "checkout", "-B", "main"], check=True)
            subprocess.run(["git", "pull"], check=True)
            bt.logging.info(f"Successfully pulled source code for main branch'.")
        else:
            subprocess.run(["git", "checkout", f"tags/{tag}"], check=True)
            bt.logging.info(f"Successfully pulled source code for tag '{tag}'.")

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
