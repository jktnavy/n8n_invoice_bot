#!/usr/bin/env python3
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT_DIR / "database" / "schema.sql").read_text()
SEQUENCE_EXAMPLE = (ROOT_DIR / "database" / "sequence-allocation.example.sql").read_text()
QUERY_DIR = ROOT_DIR / "database" / "queries"
QUERY_TEMPLATES = "\n".join(path.read_text() for path in sorted(QUERY_DIR.glob("*.sql")))
APPROVE_DRAFT_SQL = (QUERY_DIR / "approve-draft.sql").read_text()
CREATE_DRAFT_SQL = (QUERY_DIR / "create-draft.sql").read_text()
GET_STATUS_SQL = (QUERY_DIR / "get-invoice-status.sql").read_text()
VOID_INVOICE_SQL = (QUERY_DIR / "void-invoice.sql").read_text()
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

    if "UNIQUE KEY uq_invoices_source_draft (source_draft_id)" not in SCHEMA:
        raise SystemExit("invoices must uniquely bind source_draft_id to prevent duplicate approval inserts")

    if "target_chat_id" not in SCHEMA:
        raise SystemExit("invoice_deliveries must store target_chat_id")

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
    ]:
        if required_fragment not in APPROVE_DRAFT_SQL:
            raise SystemExit(f"approve-draft missing invoice number allocation fragment: {required_fragment}")

    for required_fragment in [
        "FOR UPDATE",
        "UPDATE invoices",
        "status = 'VOID'",
        "i.status <> 'VOID'",
        "c.last_invoice_id = i.id",
        ":invoice_id",
        ":invoice_number",
        ":telegram_chat_id",
    ]:
        if required_fragment not in VOID_INVOICE_SQL:
            raise SystemExit(f"void-invoice query missing fragment: {required_fragment}")

    if re.search(r"\bDELETE\b", VOID_INVOICE_SQL, re.IGNORECASE):
        raise SystemExit("void-invoice must not delete invoice records")

    print("SCHEMA_STATIC_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
