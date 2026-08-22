#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-auto}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/data/backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DB_NAME="${MYSQL_DATABASE:-invoice_bot_v2}"

mkdir -p "$BACKUP_DIR"
cd "$ROOT_DIR"
OUTPUT_PATH="$BACKUP_DIR/$DB_NAME-$STAMP.sql"

run_native() {
  if [[ -z "${MYSQL_PASSWORD:-}" ]]; then
    return 2
  fi
  mysqldump \
    -h "${MYSQL_HOST:-127.0.0.1}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_USER:-invoice_bot_v2}" \
    "-p${MYSQL_PASSWORD}" \
    "$DB_NAME" > "$OUTPUT_PATH"
}

run_compose() {
  docker compose exec -T mysql mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD:-}" "$DB_NAME" > "$OUTPUT_PATH"
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
        echo "BACKUP=SKIP native credentials missing and Docker Compose unavailable" >&2
        exit 2
      fi
    fi
    ;;
  *)
    echo "Usage: $0 [auto|native|compose]" >&2
    exit 2
    ;;
esac

printf 'Backup written: %s\n' "$OUTPUT_PATH"
