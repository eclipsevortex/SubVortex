import sys
import re
from pathlib import Path

# =====================
# Config
# =====================
pyproject_path = Path("pyproject.toml")
version_file_path = Path("VERSION")

# =====================
# Helpers
# =====================
def read_version_from_pyproject():
    content = pyproject_path.read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else None

def write_version_to_pyproject(new_version):
    content = pyproject_path.read_text()
    updated = re.sub(r'version\s*=\s*"([^"]+)"', f'version = "{new_version}"', content)
    pyproject_path.write_text(updated)

def read_version_from_file():
    return version_file_path.read_text().strip()

def write_version_to_file(new_version):
    version_file_path.write_text(f"{new_version}\n")

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
cmd = sys.argv[1] if len(sys.argv) > 1 else "patch"

source = None
if version_file_path.exists():
    version = read_version_from_file()
    source = "file"
elif pyproject_path.exists():
    version = read_version_from_pyproject()
    source = "pyproject"
else:
    print("❌ No VERSION or pyproject.toml file found.")
    sys.exit(1)

if not version:
    print("❌ No version found in the detected source.")
    sys.exit(1)

major, minor, patch, suffix, suffix_num = parse_version(version)

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
elif cmd in ["alpha", "rc", "beta"]:
    if suffix == cmd:
        suffix_num = (suffix_num or 0) + 1
    else:
        suffix = cmd
        suffix_num = 1
elif cmd == "new-prerelease":
    suffix = suffix or "alpha"
    suffix_num = (suffix_num or 0) + 1
else:
    print(f"❌ Unknown bump type: {cmd}")
    sys.exit(1)

new_version = build_version_string(major, minor, patch, suffix, suffix_num)

if source == "file":
    write_version_to_file(new_version)
elif source == "pyproject":
    write_version_to_pyproject(new_version)

print(f"✅ Version bumped to: {new_version} ({'VERSION' if source == 'file' else 'pyproject.toml'})")
