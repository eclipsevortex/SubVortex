#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE="$2"
WHEEL_IMAGE="$3"
VERSION_TAG="$4"

REPO_NAME="subvortex-$COMPONENT-${SERVICE//_/-}"
IMAGE="subvortex/$REPO_NAME"
VERSION="${VERSION_TAG#v}"
DOCKERFILE="subvortex/$COMPONENT/$SERVICE/Dockerfile"

echo "🔍 Building image for component: $COMPONENT"
echo "📦 Image name: $IMAGE"
echo "🏷️  Tag: $VERSION"

echo "📦 Extracting role version from subvortex/$COMPONENT/version.py"
ROLE_VERSION=$(python -c "import ast; f=open('subvortex/$COMPONENT/version.py'); print([n.value.s for n in ast.walk(ast.parse(f.read())) if isinstance(n, ast.Assign) and n.targets[0].id == '__version__'][0])")

echo "🔍 Searching for component version..."
COMPONENT_PATH="subvortex/$COMPONENT/$SERVICE"
if [[ -f "$COMPONENT_PATH/pyproject.toml" ]]; then
  echo "✅ Found pyproject.toml"
  COMPONENT_VERSION=$(grep -E '^version\s*=' "$COMPONENT_PATH/pyproject.toml" | head -1 | sed -E 's/version\s*=\s*"([^"]+)"/\1/')
elif [[ -f "$COMPONENT_PATH/version.py" ]]; then
  echo "✅ Found version.py"
  COMPONENT_VERSION=$(python -c "import ast; f=open('$COMPONENT_PATH/version.py'); print([n.value.s for n in ast.walk(ast.parse(f.read())) if isinstance(n, ast.Assign) and n.targets[0].id == '__version__'][0])")
else
  echo "❌ No version file found for component: $COMPONENT"
  exit 1
fi

echo "🧾 Resolved Versions:"
echo "VERSION=$VERSION"
echo "ROLE_VERSION=$ROLE_VERSION"
echo "COMPONENT_VERSION=$COMPONENT_VERSION"

# -- Check if local image already matches
LABEL_KEY="$COMPONENT.$SERVICE.version"

# Try to read the label from local docker images
EXISTING_COMPONENT_VERSION=$(docker image inspect "$IMAGE:$VERSION" --format "{{ index .Config.Labels \"$LABEL_KEY\" }}" 2>/dev/null || echo "")

if [[ "$EXISTING_COMPONENT_VERSION" == "$COMPONENT_VERSION" ]]; then
  echo "✅ Image already built for $COMPONENT/$SERVICE with version $COMPONENT_VERSION. Skipping build."
  exit 0
fi

echo "🚀 Building and pushing Docker image: $IMAGE:$VERSION"

docker buildx build \
  --squash \
  --platform linux/amd64 \
  --build-context wheelbuilder=docker-image://$WHEEL_IMAGE \
  --build-arg VERSION="$VERSION" \
  --build-arg ROLE_VERSION=$ROLE_VERSION \
  --build-arg COMPONENT_VERSION="$COMPONENT_VERSION" \
  --cache-from=type=gha,scope=wheels_${COMPONENT}_amd64 \
  --cache-to=type=gha,mode=max,scope=wheels_${COMPONENT}_amd64 \
  --tag "$IMAGE:$VERSION" \
  --file "$DOCKERFILE" \
  --push \
  .
