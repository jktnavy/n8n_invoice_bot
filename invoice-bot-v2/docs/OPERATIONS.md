# Operations

## Read-Only Discovery

Run before production changes:

```bash
./scripts/discover-environment.sh
```

Record the actual environment in deployment notes before choosing ports, paths, reverse proxy config, or service manager.

Run local/VPS V2 preflight checks:

```bash
./scripts/preflight-readiness.sh
```

This reports required command availability, planned port usage, static config validation, schema invariants, and n8n workflow export validity. It is read-only.

Static deployment template validation:

```bash
./scripts/validate-deploy-static.py
```

Security/readiness gates:

```bash
./scripts/scan-secrets.py
./scripts/readiness-gate.py
```

`readiness-gate.py` intentionally reports `V2_READY=NO` until runtime/live production gates are verified.

## Runtime Services

Recommended native services:

- `invoice-renderer.service`
- `n8n-invoice-bot-v2.service`

Renderer should bind to `127.0.0.1`. n8n should be behind the existing reverse proxy only after collision checks.

## Logs

Recommended:

```text
journalctl -u invoice-renderer.service
journalctl -u n8n-invoice-bot-v2.service
```

Application audit events belong in `audit_logs`.

## Backups

Back up only V2 database:

```text
invoice_bot_v2
```

Do not dump unrelated production databases as part of normal V2 operations.
