#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "TELEGRAM_BOT_TOKEN is required"
  exit 1
fi

PYTHONPATH="$ROOT_DIR/services/telegram-gateway" python3 -m telegram_gateway.cli get-me
