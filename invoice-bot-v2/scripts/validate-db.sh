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
if [[ ! "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "MYSQL_DATABASE must contain only letters, numbers, and underscores"
  exit 1
fi
if [[ ! "$DB_PORT" =~ ^[0-9]+$ ]]; then
  echo "MYSQL_PORT must be numeric"
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

conversation_user_key="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='${DB_NAME}' AND table_name='telegram_conversations' AND column_name='telegram_user_key' AND generation_expression LIKE '%coalesce%telegram_user_id%';")"
if [[ "$conversation_user_key" != "1" ]]; then
  echo "CONVERSATION_USER_KEY=FAIL"
  exit 1
fi

conversation_unique="$("${MYSQL[@]}" -e "SELECT COUNT(DISTINCT column_name) FROM information_schema.statistics WHERE table_schema='${DB_NAME}' AND table_name='telegram_conversations' AND index_name='uq_conversation_chat_user' AND column_name IN ('telegram_chat_id','telegram_user_key');")"
if [[ "$conversation_unique" != "2" ]]; then
  echo "CONVERSATION_UNIQUE_KEY=FAIL"
  exit 1
fi

source_draft_unique="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema='${DB_NAME}' AND table_name='invoices' AND index_name='uq_invoices_source_draft' AND column_name='source_draft_id';")"
if [[ "$source_draft_unique" != "1" ]]; then
  echo "SOURCE_DRAFT_UNIQUE_KEY=FAIL"
  exit 1
fi

sequence_seed="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM invoice_sequences WHERE company_code='STA' AND sequence_year=2026 AND last_number >= 0;")"
if [[ "$sequence_seed" != "1" ]]; then
  echo "SEQUENCE_SEED=FAIL company_code=STA sequence_year=2026"
  exit 1
fi

delivery_columns="$("${MYSQL[@]}" -e "SELECT COUNT(DISTINCT column_name) FROM information_schema.columns WHERE table_schema='${DB_NAME}' AND table_name='invoice_deliveries' AND column_name IN ('target_chat_id','provider_message_id','provider_error_message','provider_response');")"
if [[ "$delivery_columns" != "4" ]]; then
  echo "DELIVERY_COLUMNS=FAIL"
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
echo "SEQUENCE_SEED=STA:2026"
echo "CONVERSATION_UNIQUENESS=telegram_chat_id + generated telegram_user_key"
echo "FOREIGN_KEYS=$fk_count"
