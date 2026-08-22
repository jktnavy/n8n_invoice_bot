#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-auto}"
FAILED=0

cd "$ROOT_DIR"

check_http() {
  local name="$1"
  local url="$2"
  if curl -fsS "$url" >/dev/null 2>&1; then
    printf '%-18s PASS\n' "$name"
  else
    printf '%-18s FAIL\n' "$name"
    FAILED=1
  fi
}

check_mysql_native() {
  if [[ -z "${MYSQL_PASSWORD:-}" ]]; then
    return 2
  fi
  mysqladmin ping \
    -h "${MYSQL_HOST:-127.0.0.1}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_USER:-invoice_bot_v2}" \
    "-p${MYSQL_PASSWORD}" >/dev/null 2>&1
}

check_mysql_compose() {
  docker compose exec -T mysql mysqladmin ping -h localhost -uroot -p"${MYSQL_ROOT_PASSWORD:-}" >/dev/null 2>&1
}

case "$MODE" in
  native)
    if check_mysql_native; then
      printf '%-18s PASS\n' "MySQL"
    else
      printf '%-18s FAIL\n' "MySQL"
      FAILED=1
    fi
    ;;
  compose)
    if check_mysql_compose; then
      printf '%-18s PASS\n' "MySQL"
    else
      printf '%-18s FAIL\n' "MySQL"
      FAILED=1
    fi
    ;;
  auto)
    if check_mysql_native; then
      printf '%-18s PASS\n' "MySQL"
    elif command -v docker >/dev/null 2>&1 && check_mysql_compose; then
      printf '%-18s PASS\n' "MySQL"
    else
      printf '%-18s FAIL\n' "MySQL"
      FAILED=1
    fi
    ;;
  *)
    echo "Usage: $0 [auto|native|compose]" >&2
    exit 2
    ;;
esac

check_http "n8n" "http://localhost:${N8N_PORT:-5678}/healthz"
check_http "Invoice Renderer" "http://${INVOICE_RENDERER_HOST:-localhost}:${INVOICE_RENDERER_PORT:-8000}/health"

if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  if PYTHONPATH="$ROOT_DIR/services/telegram-gateway" python3 -m telegram_gateway.cli get-me >/dev/null 2>&1; then
    printf '%-18s PASS\n' "Telegram getMe"
  else
    printf '%-18s FAIL\n' "Telegram getMe"
    FAILED=1
  fi
else
  printf '%-18s SKIP\n' "Telegram getMe"
fi

if PYTHONPATH="$ROOT_DIR/services/llm-parser" python3 -m llm_parser.cli structured-smoke >/dev/null 2>&1; then
  if [[ "${LLM_PROVIDER:-openai}" != "mock" && ( -z "${LLM_API_KEY:-}" || -z "${LLM_MODEL:-}" ) ]]; then
    printf '%-18s SKIP\n' "LLM Provider"
  else
    printf '%-18s PASS\n' "LLM Provider"
  fi
else
  printf '%-18s FAIL\n' "LLM Provider"
  FAILED=1
fi

exit "$FAILED"
