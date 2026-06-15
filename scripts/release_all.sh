#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CONFIG_FILE="${REPO_ROOT}/.synology-release.env"
EXAMPLE_CONFIG_FILE="${REPO_ROOT}/.synology-release.env.example"
IMAGE_REPO="ghcr.io/maverickz7773/flight-prep"
EXPECTED_TARGET_PATH="/volume1/docker/flight-prep"
EXPECTED_PROJECT_NAME="flight-prep"
EXPECTED_CONTAINER_NAME="flight-prep"
EXPECTED_APP_URL="http://100.83.254.51:8000"
EXPECTED_HEALTH_URL="http://100.83.254.51:8000/api/health"
EXPECTED_BRANCH="main"
DRY_RUN=0
KNOWN_LOCAL_UNTRACKED=(
  "Flight-Brief-Build-Guide.html"
  "Plan Continue.txt"
  "Prompt to Continue.rtf"
)

usage() {
  cat <<'EOF'
Usage: scripts/release_all.sh [--dry-run] v1.1.9

One-command release for the flight-prep project only:
1. Runs local verification
2. Updates version.ts and compose.yaml
3. Builds/pushes the linux/amd64 GHCR image
4. Commits and pushes main for Render auto-deploy
5. Uploads compose.yaml to Synology over SSH/Tailscale
6. Refreshes only the flight-prep app on Synology
7. Verifies Synology health and frontend version

Options:
  --dry-run   Skip Docker push, git commit/push, and Synology actions
EOF
}

log() {
  printf '[release_all] %s\n' "$1"
}

fail() {
  printf '[release_all] ERROR: %s\n' "$1" >&2
  exit 1
}

require_command() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing required command: ${cmd}"
}

validate_version() {
  local version="$1"
  [[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "Version must look like v1.1.9"
}

is_known_local_untracked() {
  local path="$1"
  local item
  for item in "${KNOWN_LOCAL_UNTRACKED[@]}"; do
    if [[ "$path" == "$item" ]]; then
      return 0
    fi
  done
  return 1
}

load_config() {
  [[ -f "$CONFIG_FILE" ]] || fail "Missing ${CONFIG_FILE}. Copy ${EXAMPLE_CONFIG_FILE} and fill it in first."

  # shellcheck disable=SC1090
  source "$CONFIG_FILE"

  : "${SYNOLOGY_SSH_USER:?SYNOLOGY_SSH_USER is required in .synology-release.env}"
  : "${SYNOLOGY_SSH_HOST:?SYNOLOGY_SSH_HOST is required in .synology-release.env}"
  : "${SYNOLOGY_SSH_PORT:=22}"
  : "${SYNOLOGY_TARGET_PATH:=$EXPECTED_TARGET_PATH}"
  : "${SYNOLOGY_PROJECT_NAME:=$EXPECTED_PROJECT_NAME}"
  : "${SYNOLOGY_CONTAINER_NAME:=$EXPECTED_CONTAINER_NAME}"
  : "${SYNOLOGY_APP_URL:=$EXPECTED_APP_URL}"
  : "${SYNOLOGY_HEALTH_URL:=$EXPECTED_HEALTH_URL}"

  [[ "$SYNOLOGY_TARGET_PATH" == "$EXPECTED_TARGET_PATH" ]] || fail "Refusing to deploy to ${SYNOLOGY_TARGET_PATH}; expected ${EXPECTED_TARGET_PATH}"
  [[ "$SYNOLOGY_PROJECT_NAME" == "$EXPECTED_PROJECT_NAME" ]] || fail "Refusing to deploy project ${SYNOLOGY_PROJECT_NAME}; expected ${EXPECTED_PROJECT_NAME}"
  [[ "$SYNOLOGY_CONTAINER_NAME" == "$EXPECTED_CONTAINER_NAME" ]] || fail "Refusing to deploy container ${SYNOLOGY_CONTAINER_NAME}; expected ${EXPECTED_CONTAINER_NAME}"
}

ensure_branch() {
  local branch
  branch="$(git rev-parse --abbrev-ref HEAD)"
  [[ "$branch" == "$EXPECTED_BRANCH" ]] || fail "Current branch is ${branch}; switch to ${EXPECTED_BRANCH} before releasing"
}

ensure_no_unexpected_untracked() {
  local path
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    if is_known_local_untracked "$path"; then
      continue
    fi
    log "Will include new untracked file in release commit: ${path}"
  done < <(git ls-files --others --exclude-standard)
}

ensure_compose_targets_flight_prep() {
  grep -q '^  flight-prep:$' compose.yaml || fail "compose.yaml does not define the expected flight-prep service"
  grep -q "image: ${IMAGE_REPO}:v" compose.yaml || fail "compose.yaml is not targeting ${IMAGE_REPO}"
  grep -q '^    container_name: flight-prep$' compose.yaml || fail "compose.yaml is not targeting the flight-prep container"
}

print_release_context() {
  log "Target project: ${SYNOLOGY_PROJECT_NAME}"
  log "Synology host: ${SYNOLOGY_SSH_HOST}:${SYNOLOGY_SSH_PORT}"
  log "Synology path: ${SYNOLOGY_TARGET_PATH}"
  log "Container name: ${SYNOLOGY_CONTAINER_NAME}"
  log "Image repo: ${IMAGE_REPO}:${VERSION}"
}

run_local_checks() {
  log "Running frontend lint"
  (cd frontend && npm run lint)

  log "Running frontend build"
  (cd frontend && npm run build)

  log "Running backend airport notes regression"
  (cd backend && venv/bin/python -m unittest tests.test_airport_notes)
}

prepare_synology_release() {
  local args=("$VERSION")
  if [[ "$DRY_RUN" -eq 1 ]]; then
    args=(--skip-build "$VERSION")
  fi

  log "Preparing Synology release files"
  ./scripts/release_synology.sh "${args[@]}"
}

verify_release_files() {
  grep -q "APP_VERSION = \"${VERSION}\"" frontend/src/lib/version.ts || fail "frontend/src/lib/version.ts was not updated to ${VERSION}"
  grep -q "image: ${IMAGE_REPO}:${VERSION}" compose.yaml || fail "compose.yaml was not updated to ${IMAGE_REPO}:${VERSION}"
}

rerun_frontend_checks() {
  log "Re-running frontend lint after version bump"
  (cd frontend && npm run lint)

  log "Re-running frontend build after version bump"
  (cd frontend && npm run build)
}

commit_and_push_release() {
  local path

  log "Staging tracked release changes"
  git add -u

  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    if is_known_local_untracked "$path"; then
      continue
    fi
    git add -- "$path"
  done < <(git ls-files --others --exclude-standard)

  if git diff --cached --quiet; then
    fail "No staged changes found for release commit"
  fi

  log "Creating release commit"
  git commit -m "release: ${VERSION}"

  log "Pushing ${EXPECTED_BRANCH} to origin"
  git push origin "${EXPECTED_BRANCH}"

  log "Waiting briefly for Git push completion"
  sleep 5
}

upload_compose_to_synology() {
  log "Uploading compose.yaml to Synology"
  scp -P "$SYNOLOGY_SSH_PORT" compose.yaml "${SYNOLOGY_SSH_USER}@${SYNOLOGY_SSH_HOST}:${SYNOLOGY_TARGET_PATH}/compose.yaml"
}

refresh_synology_project() {
  local remote_compose="${SYNOLOGY_TARGET_PATH}/compose.yaml"
  local expected_image="${IMAGE_REPO}:${VERSION}"

  log "Refreshing the Synology flight-prep project"
  ssh -p "$SYNOLOGY_SSH_PORT" "${SYNOLOGY_SSH_USER}@${SYNOLOGY_SSH_HOST}" \
    TARGET_PATH="$SYNOLOGY_TARGET_PATH" \
    PROJECT_NAME="$SYNOLOGY_PROJECT_NAME" \
    CONTAINER_NAME="$SYNOLOGY_CONTAINER_NAME" \
    COMPOSE_FILE="$remote_compose" \
    EXPECTED_IMAGE="$expected_image" \
    'bash -se' <<'EOF'
set -euo pipefail

[[ "$TARGET_PATH" == "/volume1/docker/flight-prep" ]] || {
  echo "Unexpected target path: $TARGET_PATH" >&2
  exit 1
}
[[ "$PROJECT_NAME" == "flight-prep" ]] || {
  echo "Unexpected project name: $PROJECT_NAME" >&2
  exit 1
}
[[ "$CONTAINER_NAME" == "flight-prep" ]] || {
  echo "Unexpected container name: $CONTAINER_NAME" >&2
  exit 1
}
grep -q '^  flight-prep:$' "$COMPOSE_FILE"
grep -q "image: ${EXPECTED_IMAGE}" "$COMPOSE_FILE"

if sudo /usr/local/bin/docker compose version >/dev/null 2>&1; then
  DOCKER_BIN="sudo /usr/local/bin/docker"
  COMPOSE_BIN="$DOCKER_BIN compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_BIN="sudo /usr/local/bin/docker"
  COMPOSE_BIN="docker-compose"
else
  echo "Neither docker compose nor docker-compose is available on Synology" >&2
  exit 1
fi

$COMPOSE_BIN -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down --remove-orphans
$COMPOSE_BIN -p "$PROJECT_NAME" -f "$COMPOSE_FILE" pull
$COMPOSE_BIN -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d --force-recreate

running_image="$($DOCKER_BIN inspect "$CONTAINER_NAME" --format '{{.Config.Image}}')"
[[ "$running_image" == "$EXPECTED_IMAGE" ]] || {
  echo "Running image mismatch: $running_image" >&2
  exit 1
}
EOF
}

verify_synology_runtime() {
  local health_payload
  local app_html
  local cache_buster

  cache_buster="$(date +%s)"

  log "Checking Synology health endpoint"
  health_payload="$(curl -fsS "${SYNOLOGY_HEALTH_URL}?v=${cache_buster}")"
  HEALTH_PAYLOAD="$health_payload" EXPECTED_VERSION="$VERSION" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["HEALTH_PAYLOAD"])
if payload.get("status") != "ok":
    raise SystemExit("Health endpoint did not return status=ok")
PY

  log "Checking Synology frontend version"
  app_html="$(curl -fsS "${SYNOLOGY_APP_URL}?v=${cache_buster}")"
  grep -q "$VERSION" <<<"$app_html" || fail "Synology frontend did not show ${VERSION}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
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
[[ -n "$VERSION" ]] || {
  usage
  exit 1
}

validate_version "$VERSION"
require_command git
require_command python3
require_command npm
require_command curl
require_command ssh
require_command scp
ensure_branch
ensure_no_unexpected_untracked
ensure_compose_targets_flight_prep
load_config
print_release_context
run_local_checks
prepare_synology_release
verify_release_files
rerun_frontend_checks

if [[ "$DRY_RUN" -eq 1 ]]; then
  log "Dry run complete. Docker push, git push, and Synology deploy were skipped."
  exit 0
fi

commit_and_push_release
upload_compose_to_synology
refresh_synology_project
verify_synology_runtime

log "Release ${VERSION} completed successfully."
