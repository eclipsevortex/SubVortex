#!/usr/bin/env bash

set -e

echo "🔄 Updating metadata.json with versions"

# Define components and services
COMPONENTS=("miner" "validator")
declare -A SERVICES
SERVICES["miner"]="neuron"
SERVICES["validator"]="neuron redis"

# Function to extract version from common files
get_version() {
  dir="$1"
  if [ -f "$dir/pyproject.toml" ]; then
    grep -E '^version\s*=\s*"([^"]+)"' "$dir/pyproject.toml" | awk -F '"' '{print $2}'
  elif [ -f "$dir/version.py" ]; then
    grep -oE '__version__ *= *["'\'']([^"\'']+)["'\'']' "$dir/version.py" | sed -E 's/__version__ *= *["'\'']([^"\'']+)["'\'']/\1/'
  elif [ -f "$dir/VERSION" ]; then
    tr -d '\n' < "$dir/VERSION"
  else
    echo "VERSION_NOT_FOUND"
  fi
}

# Ensure jq is installed
if ! command -v jq &> /dev/null; then
  echo "❌ Error: jq is not installed. Please install jq to run this script."
  exit 1
fi

# Iterate over all components and their services
for comp in "${COMPONENTS[@]}"; do
  for svc in ${SERVICES[$comp]}; do
    dir="subvortex/$comp/$svc"
    if [ -d "$dir" ]; then
      version=$(get_version "$dir")
      if [[ "$version" == "VERSION_NOT_FOUND" ]]; then
        echo "⚠️  No version found for $dir"
        continue
      fi

      metadata_path="$dir/metadata.json"
      tmpfile=$(mktemp)

      if [ -f "$metadata_path" ]; then
        jq --arg version "$version" '.version = $version' "$metadata_path" > "$tmpfile" && mv "$tmpfile" "$metadata_path"
      else
        echo "{\"version\": \"$version\"}" > "$metadata_path"
      fi

      echo "🏷️  Updated $metadata_path with version $version"
    else
      echo "🚫 Directory not found: $dir"
    fi
  done
done

echo "✅ Done."
