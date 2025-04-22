#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE="$2"
TAG="$3"
VERSION="${TAG#v}"
REPO_NAME="subvortex-$COMPONENT-${SERVICE//_/-}"
IMAGE="subvortex/$REPO_NAME"

DOCKER_USERNAME="${DOCKER_USERNAME:-subvortex}"
DOCKER_PASSWORD="${DOCKER_PASSWORD:-}"

if [[ -z "$DOCKER_USERNAME" || -z "$DOCKER_PASSWORD" ]]; then
  echo "❌ Missing Docker credentials (DOCKER_USERNAME / DOCKER_PASSWORD)"
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

  echo "🔐 Authenticating to Docker Hub..."
  TOKEN=$(curl -s -X POST https://hub.docker.com/v2/users/login/ \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$DOCKER_USERNAME\", \"password\": \"$DOCKER_PASSWORD\"}" | jq -r .token)

  echo "🗑️ Attempting to delete $IMAGE:$tag from Docker Hub..."
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    "https://hub.docker.com/v2/repositories/$DOCKER_USERNAME/$REPO_NAME/tags/$tag/" \
    -H "Authorization: JWT $TOKEN")

  case "$RESPONSE" in
    204) echo "✅ Deleted $IMAGE:$tag" ;;
    404) echo "⚠️ Tag $IMAGE:$tag not found on Docker Hub" ;;
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
  echo "🔍 Checking if image $IMAGE:$TARGET exists..."

  if ! docker buildx imagetools inspect "$IMAGE:$TARGET" > /dev/null 2>&1; then
    echo "⚠️ Image $IMAGE:$TARGET not found — deleting stale floating tag $FTAG"
    delete_docker_tag "$FTAG"
    continue
  fi

  echo "🏷️  Re-tagging $IMAGE:$FTAG → $IMAGE:$TARGET"
  docker buildx imagetools create \
    --tag "$IMAGE:$FTAG" \
    "$IMAGE:$TARGET"
done
