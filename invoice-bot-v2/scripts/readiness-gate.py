#!/usr/bin/env python3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED_SOURCE_ARTIFACTS = {
    "schema": "database/schema.sql",
    "renderer": "services/invoice-renderer/app/main.py",
    "openai_provider": "services/llm-parser/llm_parser/openai_provider.py",
    "telegram_gateway": "services/telegram-gateway/telegram_gateway/client.py",
    "n8n_workflows": "n8n/workflows/01-telegram-router.json",
    "acceptance_sim": "services/workflow-sim/tests/test_acceptance_sim.py",
    "native_deploy": "deploy/systemd/invoice-renderer.service",
}

RUNTIME_GATES = [
    "renderer_pdf_runtime",
    "mysql_bootstrap_runtime",
    "n8n_import_runtime",
    "telegram_live_getme_and_webhook",
    "llm_live_structured_output",
    "production_read_only_discovery",
    "production_deploy",
    "live_acceptance",
    "production_regression",
]


def main() -> int:
    missing = []
    for name, relative_path in REQUIRED_SOURCE_ARTIFACTS.items():
        if not (ROOT_DIR / relative_path).exists():
            missing.append(f"{name}:{relative_path}")

    if missing:
        print("SOURCE_READINESS=FAIL")
        for item in missing:
            print(f"MISSING={item}")
        return 1

    print("SOURCE_READINESS=PASS")
    print("V2_READY=NO")
    print("UNVERIFIED_RUNTIME_GATES=" + ",".join(RUNTIME_GATES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

