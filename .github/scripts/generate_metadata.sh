#!/usr/bin/env bash

set -e

echo "🔄 Updating metadata.json with correct versions"

# Define components and their services
COMPONENTS=("miner" "validator")
declare -A SERVICES
SERVICES["miner"]="neuron"
SERVICES["validator"]="neuron redis"

# Function to extract version from a directory
get_version() {
  dir="$1"
  if [ -f "$dir/version.py" ]; then
    grep -oE '__version__ *= *["'\'']([^"\'']+)["'\'']' "$dir/version.py" | sed -E 's/__version__ *= *["'\'']([^"\'']+)["'\'']/\1/'
  elif [ -f "$dir/pyproject.toml" ]; then
    grep -E '^version\s*=\s*"([^"]+)"' "$dir/pyproject.toml" | awk -F '"' '{print $2}'
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

# Extract root project version (./version.py)
echo "📦 Extracting root project version..."
ROOT_VERSION=$(get_version ".")
if [[ "$ROOT_VERSION" == "VERSION_NOT_FOUND" ]]; then
  echo "❌ Could not find root project version."
  exit 1
fi

# Iterate over all components
for COMPONENT in "${COMPONENTS[@]}"; do
  echo "📦 Processing component: $COMPONENT"

  # Get component version (from subvortex/component/version.py)
  COMPONENT_VERSION=$(get_version "subvortex/$COMPONENT")
  if [[ "$COMPONENT_VERSION" == "VERSION_NOT_FOUND" ]]; then
    echo "⚠️ No component version found for $COMPONENT"
    continue
  fi

  # Update each service
  for SERVICE in ${SERVICES[$COMPONENT]}; do
    echo "🔍 Processing service: $COMPONENT/$SERVICE"

    SERVICE_PATH="subvortex/$COMPONENT/$SERVICE"
    if [[ ! -d "$SERVICE_PATH" ]]; then
      echo "🚫 Directory not found: $SERVICE_PATH"
      continue
    fi

    # Get service version (subvortex/component/service)
    SERVICE_VERSION=$(get_version "$SERVICE_PATH")
    if [[ "$SERVICE_VERSION" == "VERSION_NOT_FOUND" ]]; then
      echo "⚠️ No service version found for $COMPONENT/$SERVICE"
      continue
    fi

    # Metadata file
    metadata_path="$SERVICE_PATH/metadata.json"
    tmpfile=$(mktemp)

    # Build/update JSON
    if [ -f "$metadata_path" ]; then
      jq --arg root_version "$ROOT_VERSION" \
         --arg comp_version "$COMPONENT_VERSION" \
         --arg svc_version "$SERVICE_VERSION" \
         '.version = $root_version
          | ."'"$COMPONENT"'.version" = $comp_version
          | ."'"$COMPONENT"'.'"$SERVICE"'.version" = $svc_version' \
         "$metadata_path" > "$tmpfile" && mv "$tmpfile" "$metadata_path"
    else
      echo "{
  \"version\": \"$ROOT_VERSION\",
  \"$COMPONENT.version\": \"$COMPONENT_VERSION\",
  \"$COMPONENT.$SERVICE.version\": \"$SERVICE_VERSION\"
}" > "$metadata_path"
    fi

    echo "🏷️  Updated $metadata_path with:"
    echo "    ➡️ version=$ROOT_VERSION"
    echo "    ➡️ $COMPONENT.version=$COMPONENT_VERSION"
    echo "    ➡️ $COMPONENT.$SERVICE.version=$SERVICE_VERSION"
  done
done

echo "✅ Done."
