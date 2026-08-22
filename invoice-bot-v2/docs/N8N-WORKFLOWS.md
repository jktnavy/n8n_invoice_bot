# n8n Workflows

Workflow exports live in `n8n/workflows`.
Reusable Code node snippets live in `n8n/code`.

Synchronize snippets into workflow exports:

```bash
./scripts/sync-n8n-code.py
```

Validate exports:

```bash
./scripts/validate-n8n-workflows.py
```

The validator checks source-level import readiness only: required workflow
exports, workflow names, node types, required edges, synchronized Code-node
snippets, and connection graph integrity. A live n8n import/execution test is
still a separate runtime gate.

Runtime import helper:

```bash
./scripts/import-n8n-workflows.sh auto
```

The helper runs validation before import and supports native n8n or Docker
Compose mode.

Planned workflows:

```text
01-telegram-router
02-create-invoice-draft
03-update-invoice-draft
04-approve-invoice
05-send-invoice
06-resend-invoice
07-invoice-status
08-error-handler
```

Local Telegram development uses webhook mode through Cloudflare Tunnel. Polling/manual trigger is only for specific tests.

Deterministic snippets:

- `apply-patch.js`
- `calculate-invoice.js`
- `content-fingerprint.js`
- `prepare-render-request.js`
- `render-preview.js`
- `telegram-delivery-result.js`

`03-update-invoice-draft` applies an allowed patch to the active draft, then
recalculates totals, refreshes the content fingerprint, and renders a new
preview without allocating an invoice number.

`04-approve-invoice` expects the approved invoice payload loaded from the
database transaction, validates it as a full renderer request, and carries the
Telegram target chat for delivery handoff.

`content-fingerprint.js` uses Node built-in `crypto`; set:

```text
NODE_FUNCTION_ALLOW_BUILTIN=crypto
```

Database operation templates are in `database/queries/`; workflow implementation should preserve their transaction and retry semantics.
