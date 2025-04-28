#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE="$2"
TAG="$3"

VERSION="${TAG#v}"
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-eclipsevortex}"
REPO_NAME="subvortex-$COMPONENT-${SERVICE//_/-}"
IMAGE="ghcr.io/$REPO_OWNER/$REPO_NAME"

GH_TOKEN="${GH_TOKEN:-}"

if [[ -z "$GH_TOKEN" ]]; then
    echo "❌ Missing Docker credentials (GHCR_USERNAME / GHCR_TOKEN)"
    exit 1
fi

echo "🔍 Searching for Version ID corresponding to tag: $VERSION..."

# Step 1: Find the Version ID from the tag
VERSION_ID=$(gh api "user/packages/container/${REPO_NAME}/versions" \
  | jq -r --arg VERSION "$VERSION" ".[] | select(.metadata.container.tags[]? == \"$VERSION\") | .id")

if [[ -z "$VERSION_ID" ]]; then
  echo "⚠️ No Version ID found for tag: $VERSION — skipping delete."
  exit 0
fi

echo "🔍 Found Version ID: $VERSION_ID"

# Step 2: Delete by Version ID
echo "🗑️ Deleting $IMAGE:$VERSION (Version ID: $VERSION_ID) from GitHub Container Registry..."

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    -H "Authorization: Bearer $GH_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/user/packages/container/${REPO_NAME}/versions/${VERSION_ID}")

case "$RESPONSE" in
    204)
        echo "✅ Successfully deleted $IMAGE:$VERSION"
    ;;
    404)
        echo "⚠️ Version not found: $IMAGE:$VERSION (maybe already deleted)"
    ;;
    *)
        echo "❌ Failed to delete $IMAGE:$VERSION (HTTP $RESPONSE)"
        exit 1
    ;;
esac