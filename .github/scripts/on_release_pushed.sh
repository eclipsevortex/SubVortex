#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE="$2"
RAW_VERSION_TAG="$3"
IS_PRERELEASE="$4"
IS_DRAFT="$5"

REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-eclipsevortex}"
REPO_NAME="subvortex-$COMPONENT-${SERVICE//_/-}"
IMAGE="ghcr.io/$REPO_OWNER/$REPO_NAME"

if [[ "$IS_DRAFT" == "true" ]]; then
  echo "⏭️ Skipping draft release"
  exit 0
fi

echo "📦 Current release: $RAW_VERSION_TAG (prerelease=$IS_PRERELEASE)"
echo "🔍 Getting manifest for $IMAGE:$VERSION"
docker buildx imagetools inspect "$IMAGE:$VERSION"

# Fetch all GitHub releases
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
ALL_RELEASES=$(gh api "/repos/$REPO/releases" --paginate | jq -rc '[.[] | select(.draft == false)] | sort_by(.created_at) | reverse')

# Safe extract function
jq_extract_or_empty() {
  echo "$ALL_RELEASES" | jq -r "$1" | grep -v '^null$' || echo ""
}

# Determine floating tag targets
DEV_TAG=$(jq_extract_or_empty '.[0].tag_name')
STABLE_TAG=$(jq_extract_or_empty 'map(select(.tag_name | test("-alpha") | not)) | .[0].tag_name')
LATEST_TAG=$(jq_extract_or_empty 'map(select(.prerelease == false)) | .[0].tag_name')

echo "🔁 Will update Docker floating tags:"
printf "    dev     → %s\n" "${DEV_TAG:-<none>}"
printf "    stable  → %s\n" "${STABLE_TAG:-<none>}"
printf "    latest  → %s\n" "${LATEST_TAG:-<none>}"

# Retag floating tags
for FLOAT_TAG in dev stable latest; do
  case "$FLOAT_TAG" in
    dev)    TARGET_TAG="$DEV_TAG" ;;
    stable) TARGET_TAG="$STABLE_TAG" ;;
    latest) TARGET_TAG="$LATEST_TAG" ;;
  esac

  if [[ -z "$TARGET_TAG" ]]; then
    echo "⚠️ No tag found for $FLOAT_TAG — skipping"
    continue
  fi

  if [[ "$IS_PRERELEASE" == "true" && "$FLOAT_TAG" == "latest" ]]; then
    echo "⏭️ Skipping 'latest' for prerelease"
    continue
  fi

  TARGET_VERSION="${TARGET_TAG#v}"

  # 🔥 Check if the source image exists
  if ! docker buildx imagetools inspect "$IMAGE:$TARGET_VERSION" &>/dev/null; then
    echo "⚠️ Source image $IMAGE:$TARGET_VERSION does not exist — skipping $FLOAT_TAG"
    continue
  fi

  # -- Optimization: check if FLOAT_TAG already points to the correct image
  echo "🔍 Checking if $IMAGE:$FLOAT_TAG already matches $IMAGE:$TARGET_VERSION..."

  TARGET_DIGEST=$(docker buildx imagetools inspect "$IMAGE:$TARGET_VERSION" --format '{{.Manifest.Digest}}' 2>/dev/null || echo "")
  FLOAT_DIGEST=$(docker buildx imagetools inspect "$IMAGE:$FLOAT_TAG" --format '{{.Manifest.Digest}}' 2>/dev/null || echo "")

  if [[ "$TARGET_DIGEST" == "$FLOAT_DIGEST" && -n "$TARGET_DIGEST" ]]; then
    echo "✅ $IMAGE:$FLOAT_TAG already up to date. Skipping."
    continue
  fi

  echo "🔁 Retagging $IMAGE:$TARGET_VERSION as $IMAGE:$FLOAT_TAG"
  docker buildx imagetools create \
    --tag "$IMAGE:$FLOAT_TAG" \
    "$IMAGE:$TARGET_VERSION"
done