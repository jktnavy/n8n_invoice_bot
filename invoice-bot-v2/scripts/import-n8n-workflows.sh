#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-auto}"

WORKFLOWS=(
  "08-error-handler.json"
  "01-telegram-router.json"
  "02-create-invoice-draft.json"
  "03-update-invoice-draft.json"
  "04-approve-invoice.json"
  "05-send-invoice.json"
  "06-resend-invoice.json"
  "07-invoice-status.json"
)

cd "$ROOT_DIR"

python3 "$ROOT_DIR/scripts/validate-n8n-workflows.py"

run_import() {
  local workflow_file="$1"
  case "$MODE" in
    native)
      n8n import:workflow --input="$ROOT_DIR/n8n/workflows/$workflow_file"
      ;;
    compose)
      import_with_compose "$workflow_file"
      ;;
    auto)
      if command -v n8n >/dev/null 2>&1; then
        n8n import:workflow --input="$ROOT_DIR/n8n/workflows/$workflow_file"
      elif command -v docker >/dev/null 2>&1; then
        import_with_compose "$workflow_file"
      else
        echo "N8N_IMPORT=SKIP runtime command not available"
        return 2
      fi
      ;;
    *)
      echo "Usage: $0 [auto|native|compose]" >&2
      return 2
      ;;
  esac
}

import_with_compose() {
  local workflow_file="$1"
  docker compose exec -T n8n mkdir -p /home/node/.n8n/import
  docker compose cp "$ROOT_DIR/n8n/workflows/$workflow_file" "n8n:/home/node/.n8n/import/$workflow_file"
  docker compose exec -T n8n n8n import:workflow --input="/home/node/.n8n/import/$workflow_file"
}

for workflow in "${WORKFLOWS[@]}"; do
  run_import "$workflow"
done

echo "N8N_IMPORT=PASS"
