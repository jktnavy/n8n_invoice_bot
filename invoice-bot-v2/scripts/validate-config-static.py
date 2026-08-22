#!/usr/bin/env python3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED_ENV_KEYS = {
    "MYSQL_HOST": "mysql",
    "MYSQL_PORT": "3306",
    "MYSQL_PORT_PUBLISHED": "3307",
    "MYSQL_DATABASE": "invoice_bot_v2",
    "MYSQL_USER": "invoice_bot_v2",
    "MYSQL_PASSWORD": "",
    "MYSQL_ROOT_PASSWORD": "",
    "N8N_HOST": "localhost",
    "N8N_PORT": "5678",
    "N8N_PROTOCOL": "http",
    "N8N_ENCRYPTION_KEY": "",
    "NODE_FUNCTION_ALLOW_BUILTIN": "crypto",
    "WEBHOOK_URL": "",
    "TELEGRAM_BOT_TOKEN": "",
    "LLM_PROVIDER": "openai",
    "LLM_MODEL": "",
    "LLM_API_KEY": "",
    "LLM_BASE_URL": "",
    "INVOICE_RENDERER_URL": "http://invoice-renderer:8000",
    "INVOICE_RENDERER_HOST": "127.0.0.1",
    "INVOICE_RENDERER_PORT": "8000",
    "INVOICE_OUTPUT_DIR": "/data/invoices",
}

REQUIRED_GITIGNORE = {
    ".env",
    ".env.*",
    "!.env.example",
    "__pycache__/",
    ".pytest_cache/",
    "*.pyc",
    "*.pdf",
    "*.log",
    "generated/",
    "output/",
    "readiness-evidence.json",
    "readiness-evidence.*.json",
    "!docs/readiness-evidence.example.json",
    ".vscode/",
    ".idea/",
}


def main() -> int:
    env = parse_env_example(ROOT_DIR / ".env.example")
    failures = []

    for key, expected in REQUIRED_ENV_KEYS.items():
        if key not in env:
            failures.append(f"missing env key: {key}")
        elif env[key] != expected:
            failures.append(f"unexpected env default for {key}: {env[key]!r} != {expected!r}")

    gitignore_lines = set((ROOT_DIR / ".gitignore").read_text().splitlines())
    for line in REQUIRED_GITIGNORE:
        if line not in gitignore_lines:
            failures.append(f"missing .gitignore entry: {line}")

    compose = (ROOT_DIR / "docker-compose.yml").read_text()
    expected_compose_bits = [
        "MYSQL_DATABASE: ${MYSQL_DATABASE:-invoice_bot_v2}",
        "MYSQL_USER: ${MYSQL_USER:-invoice_bot_v2}",
        "${MYSQL_PORT_PUBLISHED:-3307}:3306",
        "${INVOICE_RENDERER_PORT:-8000}:8000",
        "${N8N_PORT:-5678}:5678",
        "NODE_FUNCTION_ALLOW_BUILTIN",
    ]
    for bit in expected_compose_bits:
        if bit not in compose:
            failures.append(f"missing compose config: {bit}")

    if failures:
        print("CONFIG_STATIC_VALIDATION=FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("CONFIG_STATIC_VALIDATION=PASS")
    return 0


def parse_env_example(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key] = value
    return values


if __name__ == "__main__":
    raise SystemExit(main())
