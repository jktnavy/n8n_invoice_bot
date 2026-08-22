#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

check_http() {
  local name="$1"
  local url="$2"
  if curl -fsS "$url" >/dev/null 2>&1; then
    printf '%-18s PASS\n' "$name"
  else
    printf '%-18s FAIL\n' "$name"
  fi
}

if docker compose exec -T mysql mysqladmin ping -h localhost -uroot -p"${MYSQL_ROOT_PASSWORD:-}" >/dev/null 2>&1; then
  printf '%-18s PASS\n' "MySQL"
else
  printf '%-18s FAIL\n' "MySQL"
fi

check_http "n8n" "http://localhost:${N8N_PORT:-5678}/healthz"
check_http "Invoice Renderer" "http://localhost:8000/health"

if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  check_http "Telegram getMe" "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
else
  printf '%-18s SKIP\n' "Telegram getMe"
fi

if [[ -n "${LLM_API_KEY:-}" ]]; then
  printf '%-18s TODO\n' "LLM Provider"
else
  printf '%-18s SKIP\n' "LLM Provider"
fi

