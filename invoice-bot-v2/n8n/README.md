# n8n

This directory stores exported workflow JSON files.

Workflow exports are source-controlled implementation artifacts. Code node snippets in `n8n/code` are embedded into workflow exports by `scripts/sync-n8n-code.py`.

Import order:

1. `08-error-handler.json`
2. `01-telegram-router.json`
3. Create/update/approve/send/resend/status workflows
