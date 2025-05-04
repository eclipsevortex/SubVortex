from pip._vendor.packaging.version import Version


def to_spec_version(version: str):
    version: Version = Version(version)
    return (100 * version.major) + (10 * version.minor) + (1 * version.micro)


def to_release_version(version: str):
    version: Version = Version(version)
    return f"{version.major}.{version.minor}.{version.micro}"
