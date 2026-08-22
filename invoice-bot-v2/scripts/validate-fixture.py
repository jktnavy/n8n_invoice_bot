#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "services" / "invoice-core"))

from invoice_core import InvoiceItemInput, calculate_invoice_totals, content_fingerprint


def main() -> int:
    fixture_path = ROOT_DIR / "tests" / "fixtures" / "pt-nusa-render-request.json"
    payload = json.loads(fixture_path.read_text())
    invoice = payload["invoice"]

    calculated = calculate_invoice_totals(
        [
            InvoiceItemInput(
                item.get("trip_date"),
                item["vehicle_type"],
                int(item["quantity"]),
                item.get("pickup"),
                item.get("destination"),
                int(item["unit_price"]),
            )
            for item in invoice["items"]
        ],
        int(invoice.get("discount", 0)),
        int(invoice.get("additional_fee", 0)),
    )

    assert calculated["items"][0]["line_total"] == 5_600_000
    assert calculated["items"][1]["line_total"] == 5_200_000
    assert calculated["grand_total"] == 10_800_000
    assert int(invoice["subtotal"]) == calculated["subtotal"]
    assert int(invoice["grand_total"]) == calculated["grand_total"]

    fingerprint = content_fingerprint(invoice)
    print(json.dumps({"fixture": "pt-nusa", "grand_total": calculated["grand_total"], "fingerprint": fingerprint}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

