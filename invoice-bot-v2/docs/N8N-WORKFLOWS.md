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

- `calculate-invoice.js`
- `content-fingerprint.js`
- `render-preview.js`
- `telegram-delivery-result.js`

`content-fingerprint.js` uses Node built-in `crypto`; set:

```text
NODE_FUNCTION_ALLOW_BUILTIN=crypto
```

Database operation templates are in `database/queries/`; workflow implementation should preserve their transaction and retry semantics.
