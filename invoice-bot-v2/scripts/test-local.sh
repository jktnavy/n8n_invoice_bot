#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/services/invoice-core" \
  python3 -m unittest discover -s "$ROOT_DIR/services/invoice-core/tests" -v

python3 "$ROOT_DIR/scripts/validate-fixture.py"

python3 -m compileall -q \
  "$ROOT_DIR/services/invoice-core" \
  "$ROOT_DIR/services/llm-parser" \
  "$ROOT_DIR/services/invoice-renderer/app"

for file in $(find "$ROOT_DIR" -name '*.json' -type f); do
  python3 -m json.tool "$file" >/dev/null
done

for file in "$ROOT_DIR"/n8n/code/*.js; do
  node --check "$file"
done

for file in "$ROOT_DIR"/scripts/*.sh; do
  bash -n "$file"
done

if python3 -c 'import pytest, pydantic, fastapi, weasyprint, jinja2' >/dev/null 2>&1; then
  PYTHONPATH="$ROOT_DIR/services/invoice-renderer" \
    python3 -m pytest "$ROOT_DIR/services/invoice-renderer/tests" -q
else
  echo "SKIP renderer pytest on host: dependencies are intentionally not installed on host."
fi
