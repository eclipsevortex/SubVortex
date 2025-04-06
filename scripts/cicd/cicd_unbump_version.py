import sys
import re
from pathlib import Path

# =====================
# Helpers
# =====================
def read_version_from_pyproject(path: Path):
    pyproject = path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        return match.group(1) if match else None
    return None

def write_version_to_pyproject(path: Path, new_version):
    pyproject = path / "pyproject.toml"
    content = pyproject.read_text()
    updated = re.sub(r'version\s*=\s*"([^"]+)"', f'version = "{new_version}"', content)
    pyproject.write_text(updated)

def read_version_from_file(path: Path):
    version_file = path / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return None

def write_version_to_file(path: Path, new_version):
    version_file = path / "VERSION"
    version_file.write_text(f"{new_version}\n")

def read_version_from_comp_file(path: Path):
    comp_version_file = path / "version.py"
    if comp_version_file.exists():
        content = comp_version_file.read_text().strip()
        match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        return match.group(1) if match else None
    return None

def write_version_to_comp_file(path: Path, new_version):
    comp_version_file = path / "version.py"
    content = comp_version_file.read_text()
    updated = re.sub(r'__version__\s*=\s*"([^"]+)"', f'__version__ = "{new_version}"', content)
    comp_version_file.write_text(updated)

def parse_version(version):
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.(\d+))?$'
    match = re.match(pattern, version)
    if not match:
        print(f"❌ Invalid version format: {version}")
        sys.exit(1)
    major, minor, patch = map(int, match.groups()[:3])
    suffix, suffix_num = match.group(4), match.group(5)
    return major, minor, patch, suffix, int(suffix_num) if suffix_num else None

def build_version_string(major, minor, patch, suffix=None, suffix_num=None):
    if suffix:
        return f"{major}.{minor}.{patch}-{suffix}.{suffix_num}"
    return f"{major}.{minor}.{patch}"

# =====================
# Main
# =====================
target_path_str = sys.argv[1] if len(sys.argv) > 1 else "."
cmd = sys.argv[2] if len(sys.argv) > 2 else "patch"

target_path = Path(target_path_str).resolve()

# Try reading version from various files in the target path
version, source = None, None

if (target_path / "version.py").exists():
    version = read_version_from_comp_file(target_path)
    source = "version.py"
elif (target_path / "VERSION").exists():
    version = read_version_from_file(target_path)
    source = "VERSION"
elif (target_path / "pyproject.toml").exists():
    version = read_version_from_pyproject(target_path)
    source = "pyproject.toml"

if not version:
    print(f"❌ No version found in {target_path}")
    sys.exit(1)

major, minor, patch, suffix, suffix_num = parse_version(version)

# Handle bump or unbump
if cmd == "major":
    major += 1
    minor = patch = 0
    suffix = suffix_num = None
elif cmd == "minor":
    minor += 1
    patch = 0
    suffix = suffix_num = None
elif cmd == "patch":
    patch += 1
    suffix = suffix_num = None
elif cmd == "unmajor":
    if major > 0:
        major -= 1
        minor = patch = 0
        suffix = suffix_num = None
elif cmd == "unminor":
    if minor > 0:
        minor -= 1
        patch = 0
        suffix = suffix_num = None
elif cmd == "unpatch":
    if patch > 0:
        patch -= 1
        suffix = suffix_num = None
elif cmd in ["alpha", "rc", "beta"]:
    if suffix == cmd:
        suffix_num = (suffix_num or 1) + 1
    else:
        suffix = cmd
        suffix_num = 1
elif cmd == "new-prerelease":
    suffix = suffix or "alpha"
    suffix_num = (suffix_num or 0) + 1
else:
    print(f"❌ Unknown bump type: {cmd}")
    sys.exit(1)

# Compose new version
new_version = build_version_string(major, minor, patch, suffix, suffix_num)

# Write version back
if source == "version.py":
    write_version_to_comp_file(target_path, new_version)
elif source == "VERSION":
    write_version_to_file(target_path, new_version)
elif source == "pyproject.toml":
    write_version_to_pyproject(target_path, new_version)

print(f"✅ Version updated to: {new_version} ({source} in {target_path_str})")
