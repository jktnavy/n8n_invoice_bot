#!/usr/bin/env python3
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT_DIR / "database" / "schema.sql").read_text()
SEED = (ROOT_DIR / "database" / "seed.sql").read_text()
SEQUENCE_EXAMPLE = (ROOT_DIR / "database" / "sequence-allocation.example.sql").read_text()
QUERY_DIR = ROOT_DIR / "database" / "queries"
QUERY_TEMPLATES = "\n".join(path.read_text() for path in sorted(QUERY_DIR.glob("*.sql")))
APPROVE_DRAFT_SQL = (QUERY_DIR / "approve-draft.sql").read_text()
CREATE_DRAFT_SQL = (QUERY_DIR / "create-draft.sql").read_text()
GET_STATUS_SQL = (QUERY_DIR / "get-invoice-status.sql").read_text()
VOID_INVOICE_SQL = (QUERY_DIR / "void-invoice.sql").read_text()
UPDATE_RENDER_RESULT_SQL = (QUERY_DIR / "update-render-result.sql").read_text()
UPDATE_DELIVERY_RESULT_SQL = (QUERY_DIR / "update-delivery-result.sql").read_text()
PATCH_SCHEMA = (ROOT_DIR / "llm" / "schemas" / "invoice-patch.schema.json").read_text()

REQUIRED_TABLES = {
    "customers",
    "invoice_drafts",
    "invoice_draft_items",
    "invoices",
    "invoice_items",
    "invoice_sequences",
    "telegram_conversations",
    "invoice_deliveries",
    "audit_logs",
}


def table_exists(name: str) -> bool:
    return re.search(rf"CREATE\s+TABLE\s+{re.escape(name)}\b", SCHEMA, re.IGNORECASE) is not None


def main() -> int:
    missing = sorted(table for table in REQUIRED_TABLES if not table_exists(table))
    if missing:
        raise SystemExit(f"missing required tables: {', '.join(missing)}")

    combined = f"{SCHEMA}\n{SEQUENCE_EXAMPLE}\n{QUERY_TEMPLATES}"
    if re.search(r"SELECT\s+MAX\s*\(", combined, re.IGNORECASE):
        raise SystemExit("unsafe SELECT MAX invoice-number allocation found")

    if "FOR UPDATE" not in SEQUENCE_EXAMPLE.upper():
        raise SystemExit("sequence allocation example must use FOR UPDATE")

    if "PRIMARY KEY (company_code, sequence_year)" not in SCHEMA:
        raise SystemExit("invoice_sequences must key company_code + sequence_year")

    for seed_fragment in [
        "INSERT INTO invoice_sequences",
        "VALUES ('STA', 2026, 0)",
        "ON DUPLICATE KEY UPDATE last_number = last_number",
    ]:
        if seed_fragment not in SEED:
            raise SystemExit(f"seed.sql missing invoice sequence seed fragment: {seed_fragment}")

    if "UNIQUE KEY uq_invoices_source_draft (source_draft_id)" not in SCHEMA:
        raise SystemExit("invoices must uniquely bind source_draft_id to prevent duplicate approval inserts")

    if "target_chat_id" not in SCHEMA:
        raise SystemExit("invoice_deliveries must store target_chat_id")

    if "telegram_user_key VARCHAR(64) GENERATED ALWAYS AS (COALESCE(telegram_user_id, '')) STORED" not in SCHEMA:
        raise SystemExit("telegram_conversations must normalize nullable telegram_user_id for uniqueness")

    if "UNIQUE KEY uq_conversation_chat_user (telegram_chat_id, telegram_user_key)" not in SCHEMA:
        raise SystemExit("telegram_conversations must uniquely bind chat plus normalized user key")

    for table in ["invoice_drafts", "invoices"]:
        table_match = re.search(rf"CREATE\s+TABLE\s+{table}\s*\((.*?)\)\s+ENGINE", SCHEMA, re.IGNORECASE | re.DOTALL)
        if not table_match:
            raise SystemExit(f"{table} definition not found")
        table_sql = table_match.group(1)
        for column in ["down_payment_amount", "balance_due"]:
            if column not in table_sql:
                raise SystemExit(f"{table} must store {column}")

    for query_name, query_sql in [("create-draft", CREATE_DRAFT_SQL), ("approve-draft", APPROVE_DRAFT_SQL)]:
        for column in ["down_payment_amount", "balance_due"]:
            if column not in query_sql:
                raise SystemExit(f"{query_name} query must preserve {column}")

    for required_fragment in [
        "conversation_state IN ('IDLE', 'AWAITING_APPROVAL', 'ERROR')",
        "ELSE active_draft_id",
        "ELSE conversation_state",
    ]:
        if required_fragment not in CREATE_DRAFT_SQL:
            raise SystemExit(f"create-draft query missing conversation state guard: {required_fragment}")

    for patch_term in ['"draft"', '"payment_type"', '"down_payment_amount"']:
        if patch_term not in PATCH_SCHEMA:
            raise SystemExit(f"invoice patch schema must support payment revision term {patch_term}")

    for status_fragment in [
        "c.last_invoice_id = i.id",
        "delivery_status",
        "provider_message_id",
        ":invoice_id",
        ":invoice_number",
        ":telegram_chat_id",
        "c.telegram_user_key = COALESCE(:telegram_user_id, '')",
        "i.status <> 'VOID'",
    ]:
        if status_fragment not in GET_STATUS_SQL:
            raise SystemExit(f"get-invoice-status query missing fragment: {status_fragment}")

    if ":invoice_number" in APPROVE_DRAFT_SQL:
        raise SystemExit("approve-draft must not accept invoice_number as an input parameter")

    for required_fragment in [
        "INTO @allocated_sequence",
        "LPAD(@allocated_sequence, 4, '0')",
        "UPPER(:company_code)",
        "MONTH(:invoice_date)",
        "YEAR(:invoice_date)",
        "INTO @invoice_number",
        "telegram_user_key = COALESCE(:telegram_user_id, '')",
        "d.telegram_chat_id = :telegram_chat_id",
        "d.status = 'AWAITING_APPROVAL'",
        "@invoice_id > 0",
        "SET @invoice_id = 0",
        "SET @invoice_id = IF(ROW_COUNT() = 1, LAST_INSERT_ID(), 0)",
    ]:
        if required_fragment not in APPROVE_DRAFT_SQL:
            raise SystemExit(f"approve-draft missing invoice number allocation fragment: {required_fragment}")

    guarded_writes = [
        ("customer upsert", r"FROM invoice_drafts d\s+WHERE d\.id = :draft_id\s+AND d\.telegram_chat_id = :telegram_chat_id\s+AND d\.status = 'AWAITING_APPROVAL'"),
        ("invoice insert", r"LEFT JOIN customers c ON c\.normalized_name = LOWER\(TRIM\(d\.customer_name\)\)\s+WHERE d\.id = :draft_id\s+AND d\.telegram_chat_id = :telegram_chat_id\s+AND d\.status = 'AWAITING_APPROVAL'"),
        ("draft approval update", r"UPDATE invoice_drafts\s+SET status = 'APPROVED'\s+WHERE id = :draft_id\s+AND telegram_chat_id = :telegram_chat_id\s+AND status = 'AWAITING_APPROVAL'"),
        ("conversation update", r"UPDATE telegram_conversations\s+SET active_draft_id = NULL,[\s\S]*?WHERE telegram_chat_id = :telegram_chat_id\s+AND telegram_user_key = COALESCE\(:telegram_user_id, ''\)\s+AND @invoice_id > 0"),
    ]
    for name, pattern in guarded_writes:
        if not re.search(pattern, APPROVE_DRAFT_SQL, re.IGNORECASE):
            raise SystemExit(f"approve-draft {name} must repeat draft ownership/status guard")

    for required_fragment in [
        "FOR UPDATE",
        "UPDATE invoices",
        "status = 'VOID'",
        "i.status <> 'VOID'",
        "c.last_invoice_id = i.id",
        "c.telegram_user_key = COALESCE(:telegram_user_id, '')",
        "telegram_user_key = COALESCE(:telegram_user_id, '')",
        ":invoice_id",
        ":invoice_number",
        ":telegram_chat_id",
    ]:
        if required_fragment not in VOID_INVOICE_SQL:
            raise SystemExit(f"void-invoice query missing fragment: {required_fragment}")

    if re.search(r"\bDELETE\b", VOID_INVOICE_SQL, re.IGNORECASE):
        raise SystemExit("void-invoice must not delete invoice records")

    for required_fragment in [
        ":render_succeeded",
        "WHEN :render_succeeded = TRUE THEN 'GENERATED'",
        "ELSE 'GENERATION_FAILED'",
        "pdf_sha256 REGEXP '^[a-f0-9]{64}$'",
        "pdf_size > 0",
        "status IN ('APPROVED', 'GENERATING', 'GENERATION_FAILED')",
    ]:
        if required_fragment not in UPDATE_RENDER_RESULT_SQL:
            raise SystemExit(f"update-render-result query missing fragment: {required_fragment}")
    if ":status" in UPDATE_RENDER_RESULT_SQL:
        raise SystemExit("update-render-result must derive status from render_succeeded")

    for required_fragment in [
        ":delivery_status",
        "attempt_count = attempt_count + 1",
        ":delivery_status IN ('sent', 'failed')",
        "provider_message_id = CASE WHEN :delivery_status = 'sent' THEN :provider_message_id ELSE NULL END",
        "provider_error_message = CASE WHEN :delivery_status = 'failed' THEN :provider_error_message ELSE NULL END",
        "TRIM(CAST(:provider_message_id AS CHAR)) <> ''",
        "d.status IN ('sent', 'failed')",
    ]:
        if required_fragment not in UPDATE_DELIVERY_RESULT_SQL:
            raise SystemExit(f"update-delivery-result query missing fragment: {required_fragment}")
    if ":attempt_count" in UPDATE_DELIVERY_RESULT_SQL:
        raise SystemExit("update-delivery-result must increment attempt_count in the database")

    print("SCHEMA_STATIC_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
