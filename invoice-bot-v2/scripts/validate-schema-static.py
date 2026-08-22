#!/usr/bin/env python3
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT_DIR / "database" / "schema.sql").read_text()
SEQUENCE_EXAMPLE = (ROOT_DIR / "database" / "sequence-allocation.example.sql").read_text()
QUERY_TEMPLATES = "\n".join(path.read_text() for path in sorted((ROOT_DIR / "database" / "queries").glob("*.sql")))

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

    if "target_chat_id" not in SCHEMA:
        raise SystemExit("invoice_deliveries must store target_chat_id")

    print("SCHEMA_STATIC_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
