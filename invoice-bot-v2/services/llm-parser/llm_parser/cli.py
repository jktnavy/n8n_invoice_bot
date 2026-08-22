import argparse
import json
import os

from .providers import provider_from_env

PT_NUSA_SMOKE_MESSAGE = (
    "Buat invoice PT Nusa Horizon Wisata, 2 medium bus tanggal 15 Agustus 2026 "
    "Harapan Indah Bekasi ke Cisarua Puncak harga 2,8 juta per unit, lalu "
    "tanggal 17 Agustus 2026 Cisarua Puncak ke Jakarta harga 2,6 juta per unit. "
    "Lunas tanpa DP. Include kendaraan, pengemudi, BBM. Exclude tol, parkir, tips pengemudi."
)

VALID_INTENTS = {
    "CREATE_INVOICE",
    "UPDATE_DRAFT",
    "APPROVE_DRAFT",
    "CANCEL_DRAFT",
    "RESEND_INVOICE",
    "GET_STATUS",
    "GET_INVOICE",
    "CANCEL_INVOICE",
    "HELP",
    "UNKNOWN",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM provider helper for Invoice Bot V2.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    healthcheck = subparsers.add_parser("healthcheck")
    healthcheck.add_argument(
        "--message",
        default="buat invoice untuk testing",
        help="Short message used for intent classification smoke checks.",
    )
    structured_smoke = subparsers.add_parser("structured-smoke")
    structured_smoke.add_argument(
        "--message",
        default=PT_NUSA_SMOKE_MESSAGE,
        help="Invoice creation message used for structured output smoke checks.",
    )

    args = parser.parse_args()
    if args.command == "healthcheck":
        return healthcheck_provider(args.message)
    if args.command == "structured-smoke":
        return structured_smoke_provider(args.message)
    raise AssertionError(args.command)


def healthcheck_provider(message: str) -> int:
    provider_name = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    has_live_credentials = bool(os.environ.get("LLM_API_KEY", "").strip() and os.environ.get("LLM_MODEL", "").strip())

    if provider_name != "mock" and not has_live_credentials:
        print(
            json.dumps(
                {
                    "ok": True,
                    "provider": provider_name,
                    "mode": "skipped_live_credentials_missing",
                },
                sort_keys=True,
            )
        )
        return 0

    provider = provider_from_env()
    result = provider.classify_intent(message)
    ok = result.get("intent") in VALID_INTENTS
    print(
        json.dumps(
            {
                "ok": ok,
                "provider": provider_name,
                "mode": "live" if provider_name != "mock" else "offline_mock",
                "intent": result.get("intent"),
                "schema_version": result.get("schema_version"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if ok else 1


def structured_smoke_provider(message: str) -> int:
    provider_name = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    has_live_credentials = bool(os.environ.get("LLM_API_KEY", "").strip() and os.environ.get("LLM_MODEL", "").strip())

    if provider_name != "mock" and not has_live_credentials:
        print(
            json.dumps(
                {
                    "ok": True,
                    "provider": provider_name,
                    "mode": "skipped_live_credentials_missing",
                    "checks": ["intent", "invoice_draft"],
                },
                sort_keys=True,
            )
        )
        return 0

    provider = provider_from_env()
    intent = provider.classify_intent(message)
    invoice = provider.extract_invoice(message)
    failures = validate_structured_smoke(intent, invoice)
    ok = not failures
    print(
        json.dumps(
            {
                "ok": ok,
                "provider": provider_name,
                "mode": "live" if provider_name != "mock" else "offline_mock",
                "intent": intent.get("intent"),
                "intent_schema_version": intent.get("schema_version"),
                "invoice_schema_version": invoice.get("schema_version"),
                "customer_name": invoice.get("customer", {}).get("name") if isinstance(invoice.get("customer"), dict) else None,
                "item_count": len(invoice.get("items", [])) if isinstance(invoice.get("items"), list) else 0,
                "missing_fields": invoice.get("missing_fields"),
                "failures": failures,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if ok else 1


def validate_structured_smoke(intent: dict, invoice: dict) -> list[str]:
    failures = []
    if intent.get("schema_version") != "intent.v1":
        failures.append("intent schema_version must be intent.v1")
    if intent.get("intent") != "CREATE_INVOICE":
        failures.append("intent must be CREATE_INVOICE")
    if invoice.get("schema_version") != "invoice-draft.v1":
        failures.append("invoice schema_version must be invoice-draft.v1")
    customer = invoice.get("customer") if isinstance(invoice.get("customer"), dict) else {}
    if not str(customer.get("name") or "").strip():
        failures.append("customer.name is required")
    items = invoice.get("items")
    if not isinstance(items, list) or len(items) < 1:
        failures.append("at least one invoice item is required")
    payment = invoice.get("payment") if isinstance(invoice.get("payment"), dict) else {}
    if payment.get("type") not in {"FULL_PAYMENT", "DOWN_PAYMENT", "BALANCE_PAYMENT", "UNSPECIFIED"}:
        failures.append("payment.type is invalid")
    missing_fields = invoice.get("missing_fields")
    if missing_fields:
        failures.append("missing_fields must be empty for PT Nusa smoke")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
