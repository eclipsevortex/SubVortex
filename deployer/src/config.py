import os
from dotenv import load_dotenv

# Load .env once during the first import
load_dotenv()


class Config:
    def __init__(self, config):
        self.BUMP = config.bump or os.getenv("SUBVORTEX_BUMP", "minor")
        self.PRERELEASE = config.prerelease or os.getenv("SUBVORTEX_PRERELEASE")
        self.TARGETS = config.targets or os.getenv("SUBVORTEX_TARGETS", "").split(",")

    GITHUB_REPO = os.getenv(
        "SUBVORTEX_GITHUB_REPO", "https://github.com/eclipsevortex/SubVortex.git"
    )
    GITHUB_TOKEN = os.getenv("SUBVORTEX_GITHUB_TOKEN")

    DOCKER_REPO = os.getenv("SUBVORTEX_DOCKER_REPO", "")

    DRY_RUN = os.getenv("SUBVORTEX_DRY_RUN", True)
