#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
PDF_PATH="${2:-QR 8945.pdf}"

if [[ ! -f "$PDF_PATH" ]]; then
  echo "Sample PDF not found: $PDF_PATH" >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

echo "Checking homepage at $BASE_URL"
home_status="$(curl -sS -o "$tmp_dir/home.html" -w '%{http_code}' "$BASE_URL/")"
if [[ "$home_status" != "200" ]]; then
  echo "Homepage check failed with HTTP $home_status" >&2
  exit 1
fi

echo "Checking health endpoint"
curl -sS "$BASE_URL/api/health" > "$tmp_dir/health.json"
python3 - "$tmp_dir/health.json" <<'PY'
import json
import sys
from pathlib import Path

health = json.loads(Path(sys.argv[1]).read_text())
if health.get("status") != "ok":
    raise SystemExit(f"Health endpoint returned bad status: {health}")
if health.get("operational_info_present") is not True:
    raise SystemExit(f"Operational info file is not available: {health}")
print("Health OK:", health)
PY

echo "Checking PDF parse with $PDF_PATH"
curl -sS -X POST -F "file=@${PDF_PATH}" "$BASE_URL/api/parse" > "$tmp_dir/parse.json"
python3 - "$tmp_dir/parse.json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text())
notes = payload.get("airport_notes")
if not notes:
    raise SystemExit("airport_notes missing from parse response")
if not notes.get("departure"):
    raise SystemExit("departure airport note missing from parse response")
if not notes.get("arrival"):
    raise SystemExit("arrival airport note missing from parse response")
print("Parse OK:")
print("  departure note:", notes["departure"][:80])
print("  arrival note:", notes["arrival"][:80])
PY

echo "Smoke check passed for $BASE_URL"
