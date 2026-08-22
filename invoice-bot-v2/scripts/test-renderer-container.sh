#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-invoice-renderer-test}"

cd "$ROOT_DIR"

rm -rf "$ROOT_DIR/generated"
mkdir -p "$ROOT_DIR/generated"

docker build --target test -t "$IMAGE_NAME" services/invoice-renderer
docker run --rm "$IMAGE_NAME"

docker build -t invoice-renderer-runtime services/invoice-renderer
CLI_OUTPUT="$(docker run --rm \
  -v "$ROOT_DIR/tests/fixtures:/fixtures:ro" \
  -v "$ROOT_DIR/generated:/data/invoices" \
  invoice-renderer-runtime \
  python -m app.cli /fixtures/pt-nusa-render-request.json)"

echo "$CLI_OUTPUT"

PDF_PATH="$(find "$ROOT_DIR/generated" -type f -name '*.pdf' | head -n 1)"
if [[ -z "$PDF_PATH" ]]; then
  echo "PDF_GENERATED=NO"
  exit 1
fi

export CLI_OUTPUT
CLI_FILE_NAME="$(python3 - <<'PY'
import json
import os
from pathlib import Path

payload = json.loads(os.environ["CLI_OUTPUT"])
if payload.get("ok") is not True:
    raise SystemExit("renderer CLI did not return ok=true")
for key in ["file_path", "sha256", "size"]:
    if key not in payload:
        raise SystemExit(f"renderer CLI response missing {key}")
print(Path(payload["file_path"]).name)
PY
)"
EXPECTED_FILE_NAME="INV-0001-STA-VIII-2026.pdf"
if [[ "$CLI_FILE_NAME" != "$EXPECTED_FILE_NAME" ]]; then
  echo "PDF_FILENAME=FAIL expected=$EXPECTED_FILE_NAME actual=$CLI_FILE_NAME"
  exit 1
fi

if [[ "$(basename "$PDF_PATH")" != "$EXPECTED_FILE_NAME" ]]; then
  echo "PDF_HOST_FILENAME=FAIL expected=$EXPECTED_FILE_NAME actual=$(basename "$PDF_PATH")"
  exit 1
fi

echo "PDF_GENERATED=YES"
echo "PDF_PATH=$PDF_PATH"
PDF_SIZE="$(stat -c%s "$PDF_PATH")"
echo "PDF_SIZE=$PDF_SIZE"
if [[ "$PDF_SIZE" -lt 5000 ]]; then
  echo "PDF_SIZE=FAIL too small"
  exit 1
fi
echo "PDF_TYPE=$(file -b "$PDF_PATH")"
file "$PDF_PATH"
test -s "$PDF_PATH"
head -c 4 "$PDF_PATH" | grep -q '%PDF'
PDF_SHA256="$(sha256sum "$PDF_PATH" | awk '{print $1}')"
echo "PDF_SHA256=$PDF_SHA256"

export PDF_SHA256 PDF_SIZE
python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["CLI_OUTPUT"])
if payload["sha256"] != os.environ["PDF_SHA256"]:
    raise SystemExit("renderer CLI sha256 does not match host PDF")
if int(payload["size"]) != int(os.environ["PDF_SIZE"]):
    raise SystemExit("renderer CLI size does not match host PDF")
print("PDF_METADATA=PASS")
PY
