import re


class MockProvider:
    """Deterministic provider for offline tests only."""

    def classify_intent(self, message: str) -> dict:
        text = _normalize(message)
        approvals = {"setuju", "iya", "ya", "oke", "ok", "gas", "lanjut", "sudah benar", "sip", "oke gas"}
        if text in approvals:
            intent = "APPROVE_DRAFT"
        elif re.search(r"\b(batal|cancel|batalkan)\b", text):
            intent = "CANCEL_DRAFT"
        elif re.search(r"kirim\s+(ulang|lagi)|resend", text):
            intent = "RESEND_INVOICE"
        elif re.search(r"lihat\s+detail|detail\s+invoice|tampilkan\s+invoice", text):
            intent = "GET_INVOICE"
        elif re.search(r"status|terkirim", text):
            intent = "GET_STATUS"
        elif re.search(r"ganti|ubah|revisi|jadi|tidak usah dp", text) or ("tanpa dp" in text and not re.search(r"buat|invoice|tagihan", text)):
            intent = "UPDATE_DRAFT"
        elif re.search(r"invoice|tagihan", text):
            intent = "CREATE_INVOICE"
        else:
            intent = "UNKNOWN"
        return {"schema_version": "intent.v1", "intent": intent, "confidence": 1.0, "reason": "mock deterministic rule"}

    def extract_invoice(self, message: str, context: dict | None = None) -> dict:
        text = _normalize(message)
        if "pt nusa" not in text:
            return _empty_invoice(["customer.name", "items.trip_date", "items.quantity", "items.unit_price"])
        payment_type = "DOWN_PAYMENT" if "dp" in text and "tanpa dp" not in text else "FULL_PAYMENT"
        down_payment_amount = 1000000 if payment_type == "DOWN_PAYMENT" else None
        return {
            "schema_version": "invoice-draft.v1",
            "customer": {"name": "PT Nusa Horizon Wisata" if "horizon" in text else "PT Nusa"},
            "items": [
                {
                    "trip_date": "2026-08-15",
                    "vehicle_type": "Medium Bus",
                    "quantity": 2,
                    "pickup": "Harapan Indah Bekasi",
                    "destination": "Cisarua Puncak",
                    "unit_price": 2800000,
                },
                {
                    "trip_date": "2026-08-17",
                    "vehicle_type": "Medium Bus",
                    "quantity": 2,
                    "pickup": "Cisarua Puncak",
                    "destination": "Jakarta",
                    "unit_price": 2600000,
                },
            ],
            "payment": {"type": payment_type, "down_payment_amount": down_payment_amount},
            "notes": {
                "included": ["kendaraan", "pengemudi", "BBM"],
                "excluded": ["tol", "parkir", "tips pengemudi"],
                "free_text": None,
            },
            "missing_fields": [],
        }

    def extract_patch(self, message: str, active_draft: dict) -> dict:
        text = _normalize(message)
        patches = []
        if ("tidak usah dp" in text or "tanpa dp" in text) and ("lunas" in text or "pelunasan" in text or "langsung" in text):
            patches.append({"target": "draft", "field": "payment_type", "value": "FULL_PAYMENT"})
            patches.append({"target": "draft", "field": "down_payment_amount", "value": 0})
        elif "dp" in text and ("1 juta" in text or "1jt" in text):
            patches.append({"target": "draft", "field": "payment_type", "value": "DOWN_PAYMENT"})
            patches.append({"target": "draft", "field": "down_payment_amount", "value": 1000000})
        if "tanggal pulang" in text and "18" in text:
            patches.append({"target": "item:return_trip", "field": "trip_date", "value": "2026-08-18"})
        if "harga pulang" in text and ("2,7" in text or "2.7" in text):
            patches.append({"target": "item:return_trip", "field": "unit_price", "value": 2700000})
        return {"schema_version": "invoice-patch.v1", "patches": patches, "missing_fields": [] if patches else ["patches"]}


def _normalize(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def _empty_invoice(missing_fields: list[str]) -> dict:
    return {
        "schema_version": "invoice-draft.v1",
        "customer": {"name": None},
        "items": [],
        "payment": {"type": "UNSPECIFIED", "down_payment_amount": None},
        "notes": {"included": [], "excluded": [], "free_text": None},
        "missing_fields": missing_fields,
    }
