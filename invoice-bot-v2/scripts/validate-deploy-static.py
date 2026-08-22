#!/usr/bin/env python3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

SYSTEMD_FILES = [
    ROOT_DIR / "deploy" / "systemd" / "invoice-renderer.service",
    ROOT_DIR / "deploy" / "systemd" / "n8n-invoice-bot-v2.service",
]

FORBIDDEN_SYSTEMD_FRAGMENTS = [
    "User=root",
    "Group=root",
    "0.0.0.0 --port",
    "systemctl restart nginx",
    "systemctl restart mysql",
    "reboot",
]


def main() -> int:
    failures = []

    for service_path in SYSTEMD_FILES:
        if not service_path.exists():
            failures.append(f"missing systemd template: {service_path.relative_to(ROOT_DIR)}")
            continue
        content = service_path.read_text()
        if "User=invoicebotv2" not in content:
            failures.append(f"{service_path.name}: must run as invoicebotv2")
        if "EnvironmentFile=/opt/invoice-bot-v2/.env" not in content:
            failures.append(f"{service_path.name}: must use isolated /opt/invoice-bot-v2/.env")
        if "Restart=on-failure" not in content:
            failures.append(f"{service_path.name}: must use restart-on-failure only")
        for fragment in FORBIDDEN_SYSTEMD_FRAGMENTS:
            if fragment in content:
                failures.append(f"{service_path.name}: forbidden fragment {fragment!r}")

    renderer_service = (ROOT_DIR / "deploy" / "systemd" / "invoice-renderer.service").read_text()
    if "--host 127.0.0.1" not in renderer_service:
        failures.append("invoice-renderer.service: renderer must bind 127.0.0.1")

    native_env = parse_env(ROOT_DIR / "deploy" / "native.env.example")
    expected = {
        "MYSQL_DATABASE": "invoice_bot_v2",
        "MYSQL_USER": "invoice_bot_v2",
        "INVOICE_RENDERER_HOST": "127.0.0.1",
        "INVOICE_OUTPUT_DIR": "/var/lib/invoice-bot-v2/invoices",
        "NODE_FUNCTION_ALLOW_BUILTIN": "crypto",
        "LLM_PROVIDER": "openai",
    }
    for key, value in expected.items():
        if native_env.get(key) != value:
            failures.append(f"native.env.example: {key} must be {value!r}")

    for secret_key in ["MYSQL_PASSWORD", "N8N_ENCRYPTION_KEY", "TELEGRAM_BOT_TOKEN", "LLM_API_KEY"]:
        if native_env.get(secret_key, ""):
            failures.append(f"native.env.example: {secret_key} must be blank")

    if failures:
        print("DEPLOY_STATIC_VALIDATION=FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("DEPLOY_STATIC_VALIDATION=PASS")
    return 0


def parse_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key] = value
    return values


if __name__ == "__main__":
    raise SystemExit(main())

