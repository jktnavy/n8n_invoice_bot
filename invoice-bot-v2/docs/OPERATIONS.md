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

Runtime/live gate evidence is recorded outside Git in `readiness-evidence.json`.
Use `docs/readiness-evidence.example.json` as the template, fill only
non-secret command results, then run:

```bash
./scripts/readiness-gate.py --evidence readiness-evidence.json
```

Record one verified gate after a successful runtime check:

```bash
./scripts/record-readiness-evidence.py \
  --gate renderer_pdf_runtime \
  --command "./scripts/test-renderer-container.sh" \
  --evidence "PDF_METADATA=PASS sha256=<non-secret-digest>"
```

`V2_READY=YES` is reported only when every runtime gate is marked verified with
timestamp, command, and evidence text.
Invalid evidence, secret-like values, or a command that does not match the
selected gate make `readiness-gate.py` exit non-zero.

## Runtime Services

Recommended native services:

- `invoice-renderer.service`
- `n8n-invoice-bot-v2.service`

Renderer should bind to `127.0.0.1`. n8n should be behind the existing reverse proxy only after collision checks.

Runtime healthcheck:

```bash
./scripts/healthcheck.sh
```

The script supports `auto`, `native`, and `compose` modes:

```bash
./scripts/healthcheck.sh native
./scripts/healthcheck.sh compose
```

`auto` checks MySQL with native `mysqladmin` when runtime credentials are
available, then falls back to Docker Compose only when Docker is present.
Any checked service that reports `FAIL` makes the script exit non-zero. Checks
that report `SKIP` are intentionally omitted because credentials are absent.

The LLM provider check runs the structured-output smoke test. It uses the
deterministic mock provider when `LLM_PROVIDER=mock`. For live providers it
skips safely until both `LLM_API_KEY` and `LLM_MODEL` are present, then checks
both intent classification and invoice draft extraction against the configured
provider.

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

Native backup and migration commands:

```bash
./scripts/migrate.sh native
./scripts/backup-db.sh native
```

`migrate.sh` applies `database/schema.sql` and `database/seed.sql` in both
native and Compose modes so invoice sequence bootstrap is included.

`migrate.sh native` accepts `MYSQL_MIGRATION_USER` and
`MYSQL_MIGRATION_PASSWORD` when schema bootstrap requires broader privileges
than the scoped runtime user. Keep the runtime app on `MYSQL_USER`.

Docker Compose remains available for local convenience:

```bash
./scripts/migrate.sh compose
./scripts/backup-db.sh compose
```

Do not dump unrelated production databases as part of normal V2 operations.
