#!/usr/bin/env bash

set -e

echo "🔄 Updating metadata.json and manifest.json with correct versions"

# Define components and their services
COMPONENTS=("miner" "validator")
declare -A SERVICES
SERVICES["miner"]="neuron metagraph redis"
SERVICES["validator"]="neuron metagraph redis"

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

# Helper to update a given JSON file (metadata.json or manifest.json)
update_json_file() {
  local file_path="$1"
  local component="$2"
  local service="$3"
  local root_version="$4"
  local component_version="$5"
  local service_version="$6"

  tmpfile=$(mktemp)
  if [ -f "$file_path" ]; then
    jq --arg root_version "$root_version" \
       --arg comp_version "$component_version" \
       --arg svc_version "$service_version" \
       '.version = $root_version
        | ."'"$component"'.version" = $comp_version
        | ."'"$component"'.'"$service"'.version" = $svc_version' \
       "$file_path" > "$tmpfile" && mv "$tmpfile" "$file_path"
  else
    echo "{
  \"version\": \"$root_version\",
  \"$component.version\": \"$component_version\",
  \"$component.$service.version\": \"$service_version\"
}" > "$file_path"
  fi
}

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

    for FILE in metadata.json manifest.json; do
      FILE_PATH="$SERVICE_PATH/$FILE"
      update_json_file "$FILE_PATH" "$COMPONENT" "$SERVICE" "$ROOT_VERSION" "$COMPONENT_VERSION" "$SERVICE_VERSION"
      echo "📁 Updated $FILE_PATH:"
      echo "    ➡️ version=$ROOT_VERSION"
      echo "    ➡️ $COMPONENT.version=$COMPONENT_VERSION"
      echo "    ➡️ $COMPONENT.$SERVICE.version=$SERVICE_VERSION"
    done
  done
done

echo "✅ Done."
