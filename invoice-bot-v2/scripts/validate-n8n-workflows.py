#!/usr/bin/env python3
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

FORBIDDEN_SNIPPETS = [
    "Paste n8n/code",
    "return $input.all();",
]


def main() -> int:
    workflow_dir = ROOT_DIR / "n8n" / "workflows"
    failures = []
    for path in sorted(workflow_dir.glob("*.json")):
        workflow = json.loads(path.read_text())
        if not workflow.get("name"):
            failures.append(f"{path.name}: missing workflow name")
        for node in workflow.get("nodes", []):
            js_code = node.get("parameters", {}).get("jsCode", "")
            for forbidden in FORBIDDEN_SNIPPETS:
                if forbidden in js_code:
                    failures.append(f"{path.name}/{node.get('name')}: forbidden placeholder {forbidden!r}")
    if failures:
        print("N8N_WORKFLOW_VALIDATION=FAIL")
        for failure in failures:
            print(failure)
        return 1
    print("N8N_WORKFLOW_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

