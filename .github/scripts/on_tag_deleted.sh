#!/usr/bin/env bash
set -euo pipefail

TAG="$1"
VERSION="${TAG#v}"
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-eclipsevortex}"

GH_TOKEN="${GH_TOKEN:-}"

if [[ -z "$GH_TOKEN" ]]; then
    echo "❌ Missing Docker credentials (GHCR_TOKEN)"
    exit 1
fi

echo "🔍 Looking for packages with tag: $VERSION..."

# Fetch all container packages
PACKAGES=$(curl -s -H "Authorization: Bearer $GH_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/user/packages?package_type=container" \
    | jq -r '.[] | select(.name | test("subvortex-(miner|validator)-")) | .name')

if [[ -z "$PACKAGES" ]]; then
    echo "⚠️ No matching packages found — nothing to delete."
    exit 0
fi

for PACKAGE in $PACKAGES; do
    echo "🔍 Checking package: $PACKAGE for tag: $VERSION..."

    # Fetch all versions for this package
    VERSIONS_JSON=$(curl -s -H "Authorization: Bearer $GH_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/user/packages/container/${PACKAGE}/versions")

    VERSION_ID=$(echo "$VERSIONS_JSON" | jq -r --arg VERSION "$VERSION" '.[] | select(.metadata.container.tags[]? == $VERSION) | .id')

    if [[ -n "$VERSION_ID" ]]; then
        echo "🗑️ Deleting tag $VERSION from $PACKAGE (Version ID: $VERSION_ID)..."

        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
            -H "Authorization: Bearer $GH_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/user/packages/container/${PACKAGE}/versions/${VERSION_ID}")

        case "$RESPONSE" in
            204)
                echo "✅ Successfully deleted $PACKAGE:$VERSION"
            ;;
            404)
                echo "⚠️ Version not found: $PACKAGE:$VERSION (maybe already deleted)"
            ;;
            *)
                echo "❌ Failed to delete $PACKAGE:$VERSION (HTTP $RESPONSE)"
                exit 1
            ;;
        esac
    else
        echo "⚠️ No matching version found for $PACKAGE:$VERSION — skipping."
    fi
done
