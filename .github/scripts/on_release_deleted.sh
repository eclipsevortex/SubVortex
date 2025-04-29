#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE="$2"
TAG="$3"
VERSION="${TAG#v}"
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-eclipsevortex}"
REPO_NAME="subvortex-$COMPONENT-${SERVICE//_/-}"
IMAGE="ghcr.io/$REPO_OWNER/$REPO_NAME"

GHCR_USERNAME="${GHCR_USERNAME:-}"
GHCR_TOKEN="${GHCR_TOKEN:-}"

# Always resolve the absolute path to the 'scripts' folder
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the install_skopeo.sh script
bash "$SCRIPT_DIR/install_skopeo.sh"

if [[ -z "$GHCR_USERNAME" || -z "$GHCR_TOKEN" ]]; then
  echo "❌ Missing GHCR credentials (GHCR_USERNAME / GHCR_TOKEN)"
  exit 1
fi

echo "🧹 Cleaning up release: $TAG"
echo "📦 Target image: $IMAGE"

# Fetch all GitHub releases
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
ALL_RELEASES=$(gh api "/repos/$REPO/releases" --paginate | jq -rc '[.[] | select(.draft == false)] | sort_by(.created_at) | reverse')

# Helper to safely extract tags or return empty
jq_extract_or_empty() {
  echo "$ALL_RELEASES" | jq -r "$1" | grep -v '^null$' || echo ""
}

# Determine floating tag targets
DEV_TAG=$(jq_extract_or_empty '.[0].tag_name')
STABLE_TAG=$(jq_extract_or_empty 'map(select(.tag_name | test("-alpha") | not)) | .[0].tag_name')
LATEST_TAG=$(jq_extract_or_empty 'map(select(.prerelease == false)) | .[0].tag_name')

echo "🔁 Floating tag targets:"
printf "    dev     → %s\n" "${DEV_TAG:-<none>}"
printf "    stable  → %s\n" "${STABLE_TAG:-<none>}"
printf "    latest  → %s\n" "${LATEST_TAG:-<none>}"

# Function to delete a tag via Docker Hub API
delete_docker_tag() {
  local tag="$1"

  echo "🗑️ Attempting to delete $IMAGE:$tag from GHCR..."

  # Find version ID
  VERSION_ID=$(gh api "user/packages/container/${REPO_NAME}/versions" \
    -H "Authorization: Bearer $GHCR_TOKEN" \
    | jq -r ".[] | select(.metadata.container.tags[]? == \"$tag\") | .id")

  if [[ -z "$VERSION_ID" ]]; then
    echo "⚠️ No version ID found for tag $tag — skipping delete."
    return
  fi

  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    -H "Authorization: Bearer $GHCR_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/user/packages/container/${REPO_NAME}/versions/${VERSION_ID}")

  case "$RESPONSE" in
    204) echo "✅ Deleted $IMAGE:$tag" ;;
    404) echo "⚠️ Tag $IMAGE:$tag not found on GHCR" ;;
    *)   echo "❌ Failed to delete $IMAGE:$tag (HTTP $RESPONSE)" ;;
  esac
}

# Apply floating tags or delete if no valid target
for FTAG in dev stable latest; do
  case "$FTAG" in
    dev)    TARGET="$DEV_TAG" ;;
    stable) TARGET="$STABLE_TAG" ;;
    latest) TARGET="$LATEST_TAG" ;;
  esac

  if [[ -z "$TARGET" ]]; then
    echo "⚠️ No tag found for $FTAG — skipping"
    continue
  fi

  TARGET="${TARGET#v}"

  if [[ -n "$TARGET" ]]; then
    echo "🔍 Checking if $IMAGE:$TARGET exists..."

    if skopeo inspect --raw --creds "${GHCR_USERNAME}:${GHCR_TOKEN}" docker://$IMAGE:$TARGET &>/dev/null; then
      echo "🏷️ Re-tagging $IMAGE:$FTAG → $IMAGE:$TARGET using skopeo"
      skopeo copy --all --dest-creds="${GHCR_USERNAME}:${GHCR_TOKEN}" \
        docker://$IMAGE:$TARGET \
        docker://$IMAGE:$FTAG
      echo "✅ Floating tag '$FTAG' now points to '$TARGET'"
    else
      echo "⚠️ Image $IMAGE:$TARGET does not exist — skipping $FTAG re-tag"
      delete_docker_tag "$FTAG"
    fi
  else
    echo "⚠️ No valid candidate for $FTAG — skipping"
  fi
done