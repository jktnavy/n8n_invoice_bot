#!/usr/bin/env python3
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE = ROOT_DIR / "tests" / "fixtures" / "pt-nusa-render-request.json"
RENDERER_APP_DIR = ROOT_DIR / "services" / "invoice-renderer" / "app"

REQUIRED_INVOICE_FIELDS = {
    "invoice_number",
    "invoice_date",
    "customer_name",
    "payment_type",
    "subtotal",
    "discount",
    "additional_fee",
    "grand_total",
    "items",
}

REQUIRED_ITEM_FIELDS = {
    "sort_order",
    "vehicle_type",
    "quantity",
    "uom",
    "unit_price",
    "line_total",
}

FORBIDDEN_RENDERER_PATTERNS = {
    "mysql_connector": re.compile(r"\b(mysql|mariadb|pymysql|MySQLdb|sqlalchemy)\b", re.IGNORECASE),
    "mysql_env": re.compile(r"\bMYSQL_[A-Z0-9_]+\b"),
    "sql_query": re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\s+.+\bFROM\b", re.IGNORECASE),
}


def main() -> int:
    failures = []
    request = json.loads(FIXTURE.read_text())
    invoice = request.get("invoice")
    if not isinstance(invoice, dict):
        failures.append("fixture must contain invoice object")
    else:
        failures.extend(validate_invoice_payload(invoice))

    failures.extend(validate_renderer_has_no_database_access())

    if failures:
        print("RENDERER_CONTRACT_VALIDATION=FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("RENDERER_CONTRACT_VALIDATION=PASS")
    return 0


def validate_invoice_payload(invoice: dict) -> list[str]:
    failures = []
    missing = sorted(REQUIRED_INVOICE_FIELDS - set(invoice))
    if missing:
        failures.append("fixture invoice missing fields: " + ",".join(missing))

    items = invoice.get("items")
    if not isinstance(items, list) or not items:
        failures.append("fixture invoice must include at least one item")
        return failures

    calculated_subtotal = Decimal("0")
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            failures.append(f"fixture item {index} must be an object")
            continue
        missing_item_fields = sorted(REQUIRED_ITEM_FIELDS - set(item))
        if missing_item_fields:
            failures.append(f"fixture item {index} missing fields: " + ",".join(missing_item_fields))
            continue

        quantity = decimal(item["quantity"])
        unit_price = decimal(item["unit_price"])
        line_total = decimal(item["line_total"])
        expected_line_total = quantity * unit_price
        if line_total != expected_line_total:
            failures.append(f"fixture item {index} line_total expected {expected_line_total}")
        calculated_subtotal += line_total

    subtotal = decimal(invoice.get("subtotal", "0"))
    discount = decimal(invoice.get("discount", "0"))
    additional_fee = decimal(invoice.get("additional_fee", "0"))
    grand_total = decimal(invoice.get("grand_total", "0"))

    if subtotal != calculated_subtotal:
        failures.append(f"fixture subtotal expected {calculated_subtotal}")
    expected_grand_total = subtotal - discount + additional_fee
    if grand_total != expected_grand_total:
        failures.append(f"fixture grand_total expected {expected_grand_total}")

    return failures


def validate_renderer_has_no_database_access() -> list[str]:
    failures = []
    for path in sorted(RENDERER_APP_DIR.rglob("*.py")):
        text = path.read_text()
        for name, pattern in FORBIDDEN_RENDERER_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{path.relative_to(ROOT_DIR)}: forbidden renderer database access marker {name}")
    return failures


def decimal(value) -> Decimal:
    return Decimal(str(value))


if __name__ == "__main__":
    raise SystemExit(main())
