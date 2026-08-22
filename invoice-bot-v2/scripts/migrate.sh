#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-auto}"

cd "$ROOT_DIR"

run_native() {
  local db_user="${MYSQL_MIGRATION_USER:-${MYSQL_USER:-invoice_bot_v2}}"
  local db_password="${MYSQL_MIGRATION_PASSWORD:-${MYSQL_PASSWORD:-}}"

  if [[ -z "$db_password" ]]; then
    return 2
  fi
  mysql \
    -h "${MYSQL_HOST:-127.0.0.1}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "$db_user" \
    "-p$db_password" < database/schema.sql
  mysql \
    -h "${MYSQL_HOST:-127.0.0.1}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "$db_user" \
    "-p$db_password" < database/seed.sql
}

run_compose() {
  docker compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD:-}" < database/schema.sql
  docker compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD:-}" < database/seed.sql
}

case "$MODE" in
  native)
    run_native
    ;;
  compose)
    run_compose
    ;;
  auto)
    if ! run_native; then
      if command -v docker >/dev/null 2>&1; then
        run_compose
      else
        echo "MIGRATE=SKIP native credentials missing and Docker Compose unavailable" >&2
        exit 2
      fi
    fi
    ;;
  *)
    echo "Usage: $0 [auto|native|compose]" >&2
    exit 2
    ;;
esac

echo "MIGRATE=PASS"
