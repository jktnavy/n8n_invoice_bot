from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import InvoicePayload


def payload():
    return {
        "invoice_number": "INV-0001/STA/VIII/2026",
        "invoice_date": "2026-08-22",
        "customer_name": "PT Nusa Horizon Wisata",
        "payment_type": "FULL_PAYMENT",
        "subtotal": "10800000",
        "discount": "0",
        "additional_fee": "0",
        "grand_total": "10800000",
        "included": ["kendaraan", "pengemudi", "BBM"],
        "excluded": ["tol", "parkir", "tips pengemudi"],
        "items": [
            {
                "sort_order": 1,
                "trip_date": "2026-08-15",
                "vehicle_type": "Medium Bus",
                "quantity": "2",
                "uom": "Unit",
                "pickup": "Harapan Indah Bekasi",
                "destination": "Cisarua Puncak",
                "unit_price": "2800000",
                "line_total": "5600000",
            },
            {
                "sort_order": 2,
                "trip_date": "2026-08-17",
                "vehicle_type": "Medium Bus",
                "quantity": "2",
                "uom": "Unit",
                "pickup": "Cisarua Puncak",
                "destination": "Jakarta",
                "unit_price": "2600000",
                "line_total": "5200000",
            },
        ],
    }


def test_invoice_payload_accepts_valid_fixture():
    invoice = InvoicePayload.model_validate(payload())
    assert invoice.grand_total == Decimal("10800000")


def test_invoice_payload_rejects_wrong_total():
    invalid = payload()
    invalid["grand_total"] = "1"
    with pytest.raises(ValidationError):
        InvoicePayload.model_validate(invalid)

