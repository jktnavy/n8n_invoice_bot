#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_FILE = ROOT_DIR / "readiness-evidence.json"
EVIDENCE_SCHEMA_VERSION = "invoice-bot-v2-runtime-evidence.v1"

REQUIRED_SOURCE_ARTIFACTS = {
    "schema": "database/schema.sql",
    "renderer": "services/invoice-renderer/app/main.py",
    "openai_provider": "services/llm-parser/llm_parser/openai_provider.py",
    "telegram_gateway": "services/telegram-gateway/telegram_gateway/client.py",
    "n8n_workflows": "n8n/workflows/01-telegram-router.json",
    "acceptance_sim": "services/workflow-sim/tests/test_acceptance_sim.py",
    "renderer_contract": "scripts/validate-renderer-contract.py",
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

EXPECTED_GATE_COMMAND_FRAGMENTS = {
    "renderer_pdf_runtime": ["test-renderer-container.sh"],
    "mysql_bootstrap_runtime": ["migrate.sh", "validate-db.sh"],
    "n8n_import_runtime": ["import-n8n-workflows.sh"],
    "telegram_live_getme_and_webhook": ["test-telegram.sh", "telegram-webhook.sh"],
    "llm_live_structured_output": ["llm_parser.cli structured-smoke"],
    "production_read_only_discovery": ["discover-environment.sh"],
    "production_deploy": ["healthcheck.sh"],
    "live_acceptance": ["Telegram", "scenario A-E"],
    "production_regression": ["preflight-readiness.sh", "healthcheck.sh"],
}

SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(token|password|api[_-]?key|authorization)\s*[:=]\s*\S+", re.IGNORECASE),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoice Bot V2 readiness gate.")
    parser.add_argument(
        "--evidence",
        type=Path,
        default=DEFAULT_EVIDENCE_FILE,
        help="Runtime evidence JSON. Defaults to ./readiness-evidence.json.",
    )
    args = parser.parse_args()

    missing = []
    for name, relative_path in REQUIRED_SOURCE_ARTIFACTS.items():
        if not (ROOT_DIR / relative_path).exists():
            missing.append(f"{name}:{relative_path}")

    if missing:
        print("SOURCE_READINESS=FAIL")
        for item in missing:
            print(f"MISSING={item}")
        return 1

    evidence_result = validate_runtime_evidence(args.evidence)
    verified_gates = evidence_result["verified_gates"]
    unverified_gates = [gate for gate in RUNTIME_GATES if gate not in verified_gates]

    print("SOURCE_READINESS=PASS")
    print(f"EVIDENCE_FILE={args.evidence}")
    if evidence_result["status"] == "missing":
        print("RUNTIME_EVIDENCE=MISSING")
    elif evidence_result["status"] == "invalid":
        print("RUNTIME_EVIDENCE=INVALID")
        for failure in evidence_result["failures"]:
            print(f"RUNTIME_EVIDENCE_FAILURE={failure}")
    else:
        print("RUNTIME_EVIDENCE=VALID")
    print("VERIFIED_RUNTIME_GATES=" + ",".join(verified_gates))
    print("UNVERIFIED_RUNTIME_GATES=" + ",".join(unverified_gates))
    print("V2_READY=" + ("YES" if not unverified_gates and evidence_result["status"] == "valid" else "NO"))
    return 1 if evidence_result["status"] == "invalid" else 0


def validate_runtime_evidence(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing", "verified_gates": [], "failures": []}

    failures = []
    text = path.read_text()
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            failures.append("evidence file appears to contain a secret-like value")
            break

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"status": "invalid", "verified_gates": [], "failures": [f"invalid JSON: {exc}"]}

    if payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        failures.append(f"schema_version must be {EVIDENCE_SCHEMA_VERSION}")
    if not str(payload.get("generated_at", "")).strip():
        failures.append("generated_at is required")
    if not str(payload.get("environment", "")).strip():
        failures.append("environment is required")

    gates = payload.get("gates")
    if not isinstance(gates, dict):
        failures.append("gates must be an object")
        gates = {}

    verified_gates = []
    unknown_gates = sorted(set(gates) - set(RUNTIME_GATES))
    for gate in unknown_gates:
        failures.append(f"unknown runtime gate: {gate}")

    for gate in RUNTIME_GATES:
        gate_evidence = gates.get(gate)
        if not isinstance(gate_evidence, dict):
            continue
        if gate_evidence.get("verified") is not True:
            continue
        missing_required_field = False
        for field in ["verified_at", "command", "evidence"]:
            if not str(gate_evidence.get(field, "")).strip():
                failures.append(f"{gate}: {field} is required when verified=true")
                missing_required_field = True
        command = str(gate_evidence.get("command", ""))
        for fragment in EXPECTED_GATE_COMMAND_FRAGMENTS[gate]:
            if fragment not in command:
                failures.append(f"{gate}: command must include {fragment!r}")
                missing_required_field = True
        if not missing_required_field:
            verified_gates.append(gate)

    return {"status": "invalid" if failures else "valid", "verified_gates": verified_gates, "failures": failures}


if __name__ == "__main__":
    raise SystemExit(main())
