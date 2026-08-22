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
docker run --rm \
  -v "$ROOT_DIR/tests/fixtures:/fixtures:ro" \
  -v "$ROOT_DIR/generated:/data/invoices" \
  invoice-renderer-runtime \
  python -m app.cli /fixtures/pt-nusa-render-request.json

PDF_PATH="$(find "$ROOT_DIR/generated" -type f -name '*.pdf' | head -n 1)"
if [[ -z "$PDF_PATH" ]]; then
  echo "PDF_GENERATED=NO"
  exit 1
fi

echo "PDF_GENERATED=YES"
echo "PDF_PATH=$PDF_PATH"
echo "PDF_SIZE=$(stat -c%s "$PDF_PATH")"
echo "PDF_TYPE=$(file -b "$PDF_PATH")"
file "$PDF_PATH"
test -s "$PDF_PATH"
head -c 4 "$PDF_PATH" | grep -q '%PDF'
echo "PDF_SHA256=$(sha256sum "$PDF_PATH" | awk '{print $1}')"
