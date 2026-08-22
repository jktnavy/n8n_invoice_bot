#!/usr/bin/env python3
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("telegram_token", re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b")),
    ("assigned_secret", re.compile(r"^(?:MYSQL_PASSWORD|MYSQL_ROOT_PASSWORD|TELEGRAM_BOT_TOKEN|LLM_API_KEY|N8N_ENCRYPTION_KEY|API_KEY)=\S+", re.MULTILINE)),
]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "generated",
    "output",
    "data",
    "node_modules",
}

TEXT_SUFFIXES = {
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".sql",
    ".txt",
    ".yml",
    ".yaml",
    ".js",
    ".service",
}


def main() -> int:
    findings = []
    for path in iter_files(ROOT_DIR):
        text = read_text(path)
        if text is None:
            continue
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                if is_allowed_placeholder(path, match.group(0)):
                    continue
                findings.append((path.relative_to(ROOT_DIR), line_no, name))

    if findings:
        print("SECRET_SCAN=FAIL")
        for path, line_no, name in findings:
            print(f"{path}:{line_no}: {name}")
        return 1

    print("SECRET_SCAN=PASS")
    return 0


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name.endswith(".env.example"):
            yield path


def read_text(path: Path) -> str | None:
    try:
        return path.read_text()
    except UnicodeDecodeError:
        return None


def is_allowed_placeholder(path: Path, value: str) -> bool:
    if path.name.endswith(".example") or path.name in {"native.env.example", ".env.example"}:
        return value.endswith("=")
    if value in {"MYSQL_PASSWORD=", "MYSQL_ROOT_PASSWORD=", "TELEGRAM_BOT_TOKEN=", "LLM_API_KEY=", "N8N_ENCRYPTION_KEY="}:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())

