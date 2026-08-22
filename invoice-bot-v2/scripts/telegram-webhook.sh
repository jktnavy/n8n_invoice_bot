#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "TELEGRAM_BOT_TOKEN is required"
  exit 1
fi

case "${1:-}" in
  info)
    PYTHONPATH="$ROOT_DIR/services/telegram-gateway" python3 -m telegram_gateway.cli get-webhook-info
    ;;
  set)
    if [[ -z "${2:-}" ]]; then
      echo "Usage: $0 set https://example.com/webhook"
      exit 1
    fi
    PYTHONPATH="$ROOT_DIR/services/telegram-gateway" python3 -m telegram_gateway.cli set-webhook --url "$2"
    ;;
  delete)
    PYTHONPATH="$ROOT_DIR/services/telegram-gateway" python3 -m telegram_gateway.cli delete-webhook
    ;;
  *)
    echo "Usage: $0 {info|set <https-url>|delete}"
    exit 1
    ;;
esac
