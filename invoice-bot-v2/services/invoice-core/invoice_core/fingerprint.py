import hashlib
import json
import re
import unicodedata
from decimal import Decimal


def content_fingerprint(invoice: dict) -> str:
    canonical = canonical_business_data(invoice)
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_business_data(invoice: dict) -> dict:
    items = [
        {
            "trip_date": item.get("trip_date"),
            "vehicle_type": normalize_text(item.get("vehicle_type")),
            "quantity": canonical_int(item.get("quantity")),
            "pickup": normalize_text(item.get("pickup")),
            "destination": normalize_text(item.get("destination")),
            "unit_price": canonical_int(item.get("unit_price")),
        }
        for item in invoice.get("items", [])
    ]
    items.sort(
        key=lambda item: (
            item["trip_date"] or "",
            item["vehicle_type"] or "",
            item["pickup"] or "",
            item["destination"] or "",
            item["quantity"],
            item["unit_price"],
        )
    )
    return {
        "customer": normalize_text(invoice.get("customer_name") or invoice.get("customer", {}).get("name")),
        "payment_type": normalize_enum(invoice.get("payment_type") or invoice.get("payment", {}).get("type")),
        "discount": canonical_int(invoice.get("discount", 0)),
        "additional_fee": canonical_int(invoice.get("additional_fee", 0)),
        "items": items,
    }


def normalize_text(value) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    return re.sub(r"\s+", " ", normalized)


def normalize_enum(value) -> str | None:
    if value is None:
        return None
    return str(value).strip().upper()


def canonical_int(value) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, str):
        cleaned = value.casefold().replace("rp", "").replace(" ", "")
        if "juta" in cleaned:
            return int(Decimal(cleaned.replace("juta", "").replace(",", ".")) * Decimal("1000000"))
        cleaned = cleaned.replace(".", "").replace(",", "")
        return int(Decimal(cleaned))
    return int(Decimal(str(value)))

