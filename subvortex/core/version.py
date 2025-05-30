import tomli  # Upgrade to python 3.11 and use tomllib which is integrated
from pathlib import Path
from pip._vendor.packaging.version import Version


def to_spec_version(version: str):
    version: Version = Version(version)
    return (100 * version.major) + (10 * version.minor) + (1 * version.micro)


def to_release_version(version: str):
    version: Version = Version(version)
    return f"{version.major}.{version.minor}.{version.micro}"


def get_version() -> str:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomli.load(f)
    return data["project"]["version"]
