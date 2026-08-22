import argparse
import json
import os

from .providers import provider_from_env


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM provider helper for Invoice Bot V2.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    healthcheck = subparsers.add_parser("healthcheck")
    healthcheck.add_argument(
        "--message",
        default="buat invoice untuk testing",
        help="Short message used for intent classification smoke checks.",
    )

    args = parser.parse_args()
    if args.command == "healthcheck":
        return healthcheck_provider(args.message)
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
    ok = result.get("intent") in {
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


if __name__ == "__main__":
    raise SystemExit(main())
