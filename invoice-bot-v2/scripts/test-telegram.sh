#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "TELEGRAM_BOT_TOKEN is required"
  exit 1
fi

curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
echo

