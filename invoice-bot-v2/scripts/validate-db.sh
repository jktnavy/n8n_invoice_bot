#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${MYSQL_HOST:-127.0.0.1}"
DB_PORT="${MYSQL_PORT:-3306}"
DB_NAME="${MYSQL_DATABASE:-invoice_bot_v2}"
DB_USER="${MYSQL_USER:-invoice_bot_v2}"

if [[ -z "${MYSQL_PASSWORD:-}" ]]; then
  echo "MYSQL_PASSWORD is required for DB validation"
  exit 1
fi

MYSQL=(mysql --batch --skip-column-names -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "-p${MYSQL_PASSWORD}" "$DB_NAME")

EXPECTED_TABLES=(
  customers
  invoice_drafts
  invoice_draft_items
  invoices
  invoice_items
  invoice_sequences
  telegram_conversations
  invoice_deliveries
  audit_logs
)

for table in "${EXPECTED_TABLES[@]}"; do
  count="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name='${table}';")"
  if [[ "$count" != "1" ]]; then
    echo "TABLE_MISSING=$table"
    exit 1
  fi
done

sequence_pk="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema='${DB_NAME}' AND table_name='invoice_sequences' AND index_name='PRIMARY' AND column_name IN ('company_code','sequence_year');")"
if [[ "$sequence_pk" != "2" ]]; then
  echo "SEQUENCE_PRIMARY_KEY=FAIL"
  exit 1
fi

fk_count="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema='${DB_NAME}';")"
if [[ "$fk_count" -lt 5 ]]; then
  echo "FOREIGN_KEYS=FAIL count=$fk_count"
  exit 1
fi

echo "MYSQL_BOOTSTRAP=PASS"
echo "DATABASE=$DB_NAME"
printf 'TABLES=%s\n' "${EXPECTED_TABLES[*]}"
echo "SEQUENCE_STRATEGY=invoice_sequences primary key + transaction FOR UPDATE"
echo "FOREIGN_KEYS=$fk_count"

