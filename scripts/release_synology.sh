#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

IMAGE_REPO="ghcr.io/maverickz7773/flight-prep"
PLATFORM="linux/amd64"
SKIP_BUILD=0

usage() {
  cat <<'EOF'
Usage: scripts/release_synology.sh [--skip-build] v1.1.2

Options:
  --skip-build   Update version.ts and compose.yaml without building/pushing Docker
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

VERSION="${1:-}"

if [[ -z "$VERSION" ]]; then
  usage
  exit 1
fi

if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v1.1.2"
  exit 1
fi

if [[ ! -f compose.yaml ]]; then
  echo "compose.yaml not found in repo root"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

if [[ "$SKIP_BUILD" -eq 0 ]] && ! command -v docker >/dev/null 2>&1; then
  echo "docker is required"
  exit 1
fi

IMAGE_TAG="${IMAGE_REPO}:${VERSION}"

python3 - <<'PY' "$VERSION"
from pathlib import Path
import re
import sys

version = sys.argv[1]
version_file = Path("frontend/src/lib/version.ts")
text = version_file.read_text()
updated = re.sub(r'APP_VERSION = "v[^"]+"', f'APP_VERSION = "{version}"', text)
if text != updated:
    version_file.write_text(updated)
PY

python3 - <<'PY' "$IMAGE_TAG"
from pathlib import Path
import re
import sys

image_tag = sys.argv[1]
compose_file = Path("compose.yaml")
text = compose_file.read_text()
updated = re.sub(
    r'image:\s*ghcr\.io/maverickz7773/flight-prep:v[0-9]+\.[0-9]+\.[0-9]+',
    f'image: {image_tag}',
    text,
)
if text == updated:
    raise SystemExit("compose.yaml image tag was not updated")
compose_file.write_text(updated)
PY

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  echo "Building and pushing ${IMAGE_TAG} for ${PLATFORM}..."
  docker buildx build \
    --platform "${PLATFORM}" \
    -t "${IMAGE_TAG}" \
    --push \
    .
else
  echo "Skipping Docker build/push; release files updated only."
fi

echo
echo "Synology release prepared:"
echo "- frontend/src/lib/version.ts updated to ${VERSION}"
echo "- compose.yaml updated to ${IMAGE_TAG}"

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  echo
  echo "Next steps:"
  echo "1. Commit and push the repo changes."
  echo "2. Upload compose.yaml to /volume1/docker/flight-prep on Synology."
  echo "3. Refresh the flight-prep project on Synology."
fi
