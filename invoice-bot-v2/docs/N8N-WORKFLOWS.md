# n8n Workflows

Workflow exports live in `n8n/workflows`.
Reusable Code node snippets live in `n8n/code`.

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
