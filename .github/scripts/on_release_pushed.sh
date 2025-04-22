#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE="$2"
RAW_VERSION_TAG="$3"
IS_PRERELEASE="$4"
IS_DRAFT="$5"

VERSION="${RAW_VERSION_TAG#v}"
REPO_NAME="subvortex-$COMPONENT-${SERVICE//_/-}"
IMAGE="subvortex/$REPO_NAME"

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
  echo "🔁 Creating manifest for $IMAGE:$FLOAT_TAG from $IMAGE:$TARGET_VERSION"
  docker buildx imagetools create \
    --tag "$IMAGE:$FLOAT_TAG" \
    "$IMAGE:$TARGET_VERSION"
done
