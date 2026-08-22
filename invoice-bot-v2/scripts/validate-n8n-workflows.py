#!/usr/bin/env python3
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

FORBIDDEN_SNIPPETS = [
    "Paste n8n/code",
    "return $input.all();",
]

WORKFLOW_CONTRACTS = {
    "01-telegram-router.json": {
        "name": "01-telegram-router",
        "nodes": {
            "Manual Test Trigger": "n8n-nodes-base.manualTrigger",
            "Normalize Telegram Message": "n8n-nodes-base.code",
            "Intent Prefilter": "n8n-nodes-base.code",
        },
        "edges": [
            ("Manual Test Trigger", "Normalize Telegram Message"),
            ("Normalize Telegram Message", "Intent Prefilter"),
        ],
        "code_contains": {
            "Normalize Telegram Message": ["telegram_chat_id", "correlation_id"],
            "Intent Prefilter": ["CREATE_INVOICE", "APPROVE_DRAFT", "UPDATE_DRAFT", "tidak usah dp"],
        },
    },
    "02-create-invoice-draft.json": {
        "name": "02-create-invoice-draft",
        "nodes": {
            "Execute Workflow Trigger": "n8n-nodes-base.executeWorkflowTrigger",
            "Business Validation": "n8n-nodes-base.code",
            "Calculate Invoice": "n8n-nodes-base.code",
            "Content Fingerprint": "n8n-nodes-base.code",
            "Render Preview": "n8n-nodes-base.code",
        },
        "edges": [
            ("Execute Workflow Trigger", "Business Validation"),
            ("Business Validation", "Calculate Invoice"),
            ("Calculate Invoice", "Content Fingerprint"),
            ("Content Fingerprint", "Render Preview"),
        ],
        "snippet_files": {
            "Calculate Invoice": "n8n/code/calculate-invoice.js",
            "Content Fingerprint": "n8n/code/content-fingerprint.js",
            "Render Preview": "n8n/code/render-preview.js",
        },
    },
    "03-update-invoice-draft.json": {
        "name": "03-update-invoice-draft",
        "nodes": {
            "Execute Workflow Trigger": "n8n-nodes-base.executeWorkflowTrigger",
            "Guard Active Draft": "n8n-nodes-base.code",
            "Apply Patch": "n8n-nodes-base.code",
            "Calculate Invoice": "n8n-nodes-base.code",
            "Content Fingerprint": "n8n-nodes-base.code",
            "Render Preview": "n8n-nodes-base.code",
        },
        "edges": [
            ("Execute Workflow Trigger", "Guard Active Draft"),
            ("Guard Active Draft", "Apply Patch"),
            ("Apply Patch", "Calculate Invoice"),
            ("Calculate Invoice", "Content Fingerprint"),
            ("Content Fingerprint", "Render Preview"),
        ],
        "code_contains": {
            "Guard Active Draft": ["active_draft_id", "AWAITING_APPROVAL"],
        },
        "snippet_files": {
            "Apply Patch": "n8n/code/apply-patch.js",
            "Calculate Invoice": "n8n/code/calculate-invoice.js",
            "Content Fingerprint": "n8n/code/content-fingerprint.js",
            "Render Preview": "n8n/code/render-preview.js",
        },
    },
    "04-approve-invoice.json": {
        "name": "04-approve-invoice",
        "nodes": {
            "Execute Workflow Trigger": "n8n-nodes-base.executeWorkflowTrigger",
            "Approval Guard": "n8n-nodes-base.code",
            "Prepare Render Request": "n8n-nodes-base.code",
        },
        "edges": [
            ("Execute Workflow Trigger", "Approval Guard"),
            ("Approval Guard", "Prepare Render Request"),
        ],
        "code_contains": {
            "Approval Guard": ["AWAITING_APPROVAL", "approval_received"],
        },
        "snippet_files": {
            "Prepare Render Request": "n8n/code/prepare-render-request.js",
        },
    },
    "05-send-invoice.json": {
        "name": "05-send-invoice",
        "nodes": {
            "Execute Workflow Trigger": "n8n-nodes-base.executeWorkflowTrigger",
            "Delivery Guard": "n8n-nodes-base.code",
            "Prepare Telegram Document": "n8n-nodes-base.code",
            "Parse Telegram Delivery Result": "n8n-nodes-base.code",
        },
        "edges": [
            ("Execute Workflow Trigger", "Delivery Guard"),
            ("Delivery Guard", "Prepare Telegram Document"),
            ("Prepare Telegram Document", "Parse Telegram Delivery Result"),
        ],
        "snippet_files": {
            "Prepare Telegram Document": "n8n/code/prepare-telegram-document.js",
            "Parse Telegram Delivery Result": "n8n/code/telegram-delivery-result.js",
        },
        "code_contains": {
            "Delivery Guard": ["invoice_id", "pdf_path", "target_chat_id"],
        },
    },
    "06-resend-invoice.json": {
        "name": "06-resend-invoice",
        "nodes": {
            "Execute Workflow Trigger": "n8n-nodes-base.executeWorkflowTrigger",
            "Resend Guard": "n8n-nodes-base.code",
        },
        "edges": [("Execute Workflow Trigger", "Resend Guard")],
        "code_contains": {
            "Resend Guard": ["invoice_number", "resend_requested"],
        },
    },
    "07-invoice-status.json": {
        "name": "07-invoice-status",
        "nodes": {
            "Execute Workflow Trigger": "n8n-nodes-base.executeWorkflowTrigger",
            "Status Guard": "n8n-nodes-base.code",
        },
        "edges": [("Execute Workflow Trigger", "Status Guard")],
        "code_contains": {
            "Status Guard": ["invoice_number", "last_invoice_id", "status_lookup_requested"],
        },
    },
    "08-error-handler.json": {
        "name": "08-error-handler",
        "nodes": {
            "Error Trigger": "n8n-nodes-base.errorTrigger",
            "Sanitize Error": "n8n-nodes-base.code",
        },
        "edges": [("Error Trigger", "Sanitize Error")],
        "code_contains": {
            "Sanitize Error": ["redacted", "correlation_id", "ERROR"],
        },
    },
}


def main() -> int:
    workflow_dir = ROOT_DIR / "n8n" / "workflows"
    failures = []
    paths = {path.name: path for path in workflow_dir.glob("*.json")}
    for required_file in WORKFLOW_CONTRACTS:
        if required_file not in paths:
            failures.append(f"{required_file}: missing required workflow export")
    for path in sorted(paths.values()):
        workflow = json.loads(path.read_text())
        if not workflow.get("name"):
            failures.append(f"{path.name}: missing workflow name")
        failures.extend(validate_graph_integrity(path.name, workflow))
        contract = WORKFLOW_CONTRACTS.get(path.name)
        if contract:
            failures.extend(validate_contract(path.name, workflow, contract))
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


def validate_contract(file_name: str, workflow: dict, contract: dict) -> list[str]:
    failures = []
    expected_name = contract["name"]
    if workflow.get("name") != expected_name:
        failures.append(f"{file_name}: expected workflow name {expected_name!r}")

    nodes = {node.get("name"): node for node in workflow.get("nodes", [])}
    for node_name, expected_type in contract["nodes"].items():
        node = nodes.get(node_name)
        if not node:
            failures.append(f"{file_name}: missing node {node_name!r}")
            continue
        if node.get("type") != expected_type:
            failures.append(f"{file_name}/{node_name}: expected type {expected_type!r}")
        if expected_type == "n8n-nodes-base.code" and not node.get("parameters", {}).get("jsCode"):
            failures.append(f"{file_name}/{node_name}: missing jsCode")

    for source, target in contract.get("edges", []):
        if not has_edge(workflow, source, target):
            failures.append(f"{file_name}: missing edge {source!r} -> {target!r}")

    for node_name, required_terms in contract.get("code_contains", {}).items():
        js_code = nodes.get(node_name, {}).get("parameters", {}).get("jsCode", "")
        for term in required_terms:
            if term not in js_code:
                failures.append(f"{file_name}/{node_name}: missing code term {term!r}")

    for node_name, snippet_file in contract.get("snippet_files", {}).items():
        expected_code = (ROOT_DIR / snippet_file).read_text().strip()
        actual_code = nodes.get(node_name, {}).get("parameters", {}).get("jsCode", "").strip()
        if actual_code != expected_code:
            failures.append(f"{file_name}/{node_name}: jsCode is not synchronized with {snippet_file}")

    return failures


def validate_graph_integrity(file_name: str, workflow: dict) -> list[str]:
    failures = []
    nodes = workflow.get("nodes", [])
    node_names = [node.get("name") for node in nodes]
    known_nodes = set(node_names)

    for node_name in sorted({name for name in node_names if node_names.count(name) > 1}):
        failures.append(f"{file_name}: duplicate node name {node_name!r}")

    for source, source_connections in workflow.get("connections", {}).items():
        if source not in known_nodes:
            failures.append(f"{file_name}: connection source {source!r} has no matching node")
        for output_group in source_connections.get("main", []):
            for edge in output_group:
                target = edge.get("node")
                if target not in known_nodes:
                    failures.append(f"{file_name}: connection target {target!r} has no matching node")
                if edge.get("type") != "main":
                    failures.append(f"{file_name}: unsupported connection type {edge.get('type')!r}")

    return failures


def has_edge(workflow: dict, source: str, target: str) -> bool:
    connections = workflow.get("connections", {}).get(source, {}).get("main", [])
    for output_group in connections:
        for edge in output_group:
            if edge.get("node") == target and edge.get("type") == "main":
                return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
