#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

printf 'INVOICE_BOT_V2_PREFLIGHT\n'
printf 'cwd=%s\n' "$ROOT_DIR"
printf 'git_sha=%s\n' "$(git rev-parse HEAD 2>/dev/null || echo unknown)"

check_command() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '%-20s AVAILABLE %s\n' "$name" "$(command -v "$name")"
  else
    printf '%-20s MISSING\n' "$name"
  fi
}

check_docker() {
  if command -v docker >/dev/null 2>&1; then
    printf 'DOCKER_AVAILABLE=YES\n'
    docker --version
    docker compose version
  else
    printf 'DOCKER_AVAILABLE=NO\n'
    printf 'DOCKER_REQUIRED=Install Docker Desktop and enable WSL integration for this distro, then rerun docker --version and docker compose version.\n'
  fi
}

check_port() {
  local port="$1"
  if ss -lnt "( sport = :$port )" | grep -q ":$port"; then
    printf 'PORT %-15s IN_USE\n' "$port"
  else
    printf 'PORT %-15s FREE\n' "$port"
  fi
}

check_command docker
check_docker
check_command python3
check_command node
check_command mysql
check_command n8n
check_command nginx

check_port "${MYSQL_PORT_PUBLISHED:-3307}"
check_port "${INVOICE_RENDERER_PORT:-8000}"
check_port "${N8N_PORT:-5678}"

./scripts/validate-config-static.py
./scripts/validate-deploy-static.py
./scripts/validate-schema-static.py
./scripts/validate-renderer-contract.py
./scripts/validate-n8n-workflows.py
./scripts/scan-secrets.py
./scripts/readiness-gate.py

printf 'PREFLIGHT_DONE\n'
