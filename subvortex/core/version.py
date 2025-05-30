from pip._vendor.packaging.version import Version
from importlib.metadata import version, PackageNotFoundError


def to_spec_version(version: str):
    version: Version = Version(version)
    return (100 * version.major) + (10 * version.minor) + (1 * version.micro)


def to_release_version(version: str):
    version: Version = Version(version)
    return f"{version.major}.{version.minor}.{version.micro}"


def get_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "unknown"
