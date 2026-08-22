#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_FILE = ROOT_DIR / "readiness-evidence.json"
DEFAULT_TEMPLATE_FILE = ROOT_DIR / "docs" / "readiness-evidence.example.json"
EVIDENCE_SCHEMA_VERSION = "invoice-bot-v2-runtime-evidence.v1"

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

SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(token|password|api[_-]?key|authorization)\s*[:=]\s*\S+", re.IGNORECASE),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Record non-secret runtime readiness evidence for Invoice Bot V2.")
    parser.add_argument("--gate", required=True, choices=RUNTIME_GATES, help="Runtime gate to mark verified.")
    parser.add_argument("--command", required=True, help="Command that was executed for this gate.")
    parser.add_argument("--evidence", required=True, help="Short non-secret evidence text from the command output.")
    parser.add_argument("--environment", default="local-or-vps", help="Environment label stored in the evidence file.")
    parser.add_argument("--file", type=Path, default=DEFAULT_EVIDENCE_FILE, help="Evidence JSON file to update.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_FILE, help="Template used when evidence file is absent.")
    args = parser.parse_args()

    assert_no_secret_like_value(args.command, "command")
    assert_no_secret_like_value(args.evidence, "evidence")

    payload = load_or_initialize_payload(args.file, args.template, args.environment)
    payload["environment"] = args.environment
    payload["generated_at"] = now_iso()
    payload.setdefault("gates", {})
    payload["gates"].setdefault(args.gate, {})
    payload["gates"][args.gate].update(
        {
            "verified": True,
            "verified_at": payload["generated_at"],
            "command": args.command,
            "evidence": args.evidence,
        }
    )

    args.file.parent.mkdir(parents=True, exist_ok=True)
    args.file.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"READINESS_EVIDENCE_UPDATED={args.file}")
    print(f"GATE_VERIFIED={args.gate}")
    return 0


def load_or_initialize_payload(path: Path, template: Path, environment: str) -> dict:
    if path.exists():
        payload = json.loads(path.read_text())
    elif template.exists():
        payload = json.loads(template.read_text())
    else:
        payload = {"schema_version": EVIDENCE_SCHEMA_VERSION, "generated_at": "", "environment": environment, "gates": {}}

    if payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise SystemExit(f"schema_version must be {EVIDENCE_SCHEMA_VERSION}")
    if not isinstance(payload.get("gates"), dict):
        raise SystemExit("gates must be an object")
    unknown_gates = sorted(set(payload["gates"]) - set(RUNTIME_GATES))
    if unknown_gates:
        raise SystemExit("unknown runtime gates: " + ",".join(unknown_gates))
    return payload


def assert_no_secret_like_value(value: str, field_name: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(value):
            raise SystemExit(f"{field_name} appears to contain a secret-like value")


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
