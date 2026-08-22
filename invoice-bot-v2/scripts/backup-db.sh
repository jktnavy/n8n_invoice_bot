#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/data/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"
cd "$ROOT_DIR"
docker compose exec -T mysql mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD:-}" invoice_bot_v2 > "$BACKUP_DIR/invoice_bot_v2-$STAMP.sql"
printf 'Backup written: %s\n' "$BACKUP_DIR/invoice_bot_v2-$STAMP.sql"

