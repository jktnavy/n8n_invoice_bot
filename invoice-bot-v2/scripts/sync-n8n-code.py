#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

WORKFLOW_CODE_MAP = {
    "01-telegram-router.json": {
        "Normalize Telegram Message": "normalize-telegram-message.js",
        "Intent Prefilter": "intent-prefilter.js",
    },
    "02-create-invoice-draft.json": {
        "Calculate Invoice": "calculate-invoice.js",
        "Content Fingerprint": "content-fingerprint.js",
        "Render Preview": "render-preview.js",
    },
    "03-update-invoice-draft.json": {
        "Apply Patch": "apply-patch.js",
        "Calculate Invoice": "calculate-invoice.js",
        "Content Fingerprint": "content-fingerprint.js",
        "Render Preview": "render-preview.js",
    },
    "04-approve-invoice.json": {
        "Prepare Render Request": "prepare-render-request.js",
    },
    "05-send-invoice.json": {
        "Prepare Telegram Document": "prepare-telegram-document.js",
        "Parse Telegram Delivery Result": "telegram-delivery-result.js",
    },
    "06-resend-invoice.json": {
        "Prepare Telegram Document": "prepare-telegram-document.js",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed canonical n8n Code snippets into workflow exports.")
    parser.add_argument("--check", action="store_true", help="Fail if workflow exports are not synchronized.")
    args = parser.parse_args()

    changed = []
    for workflow_name, node_map in WORKFLOW_CODE_MAP.items():
        workflow_path = ROOT_DIR / "n8n" / "workflows" / workflow_name
        workflow = json.loads(workflow_path.read_text())
        original = json.dumps(workflow, sort_keys=True)

        for node in workflow.get("nodes", []):
            snippet_name = node_map.get(node.get("name"))
            if not snippet_name:
                continue
            snippet = (ROOT_DIR / "n8n" / "code" / snippet_name).read_text().rstrip() + "\n"
            node.setdefault("parameters", {})["jsCode"] = snippet

        rendered = json.dumps(workflow, indent=2, ensure_ascii=False) + "\n"
        if json.dumps(workflow, sort_keys=True) != original:
            changed.append(str(workflow_path.relative_to(ROOT_DIR)))
            if not args.check:
                workflow_path.write_text(rendered)
        elif not args.check:
            workflow_path.write_text(rendered)

    if args.check and changed:
        print("N8N_CODE_SYNC=FAIL")
        for path in changed:
            print(f"OUT_OF_SYNC={path}")
        return 1

    print("N8N_CODE_SYNC=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
