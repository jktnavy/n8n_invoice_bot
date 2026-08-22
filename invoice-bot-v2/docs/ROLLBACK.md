# Rollback

V2 is isolated from the legacy Hermes flow. Rollback means disabling V2 without deleting legacy.

Safe rollback sequence:

```text
1. Disable Telegram webhook for V2 or stop n8n V2 workflow.
2. Stop invoice-renderer.service.
3. Stop n8n-invoice-bot-v2.service only if it is a dedicated V2 service.
4. Leave invoice_bot_v2 database intact for audit.
5. Confirm legacy invoice bot remains available before any cutover cleanup.
```

Do not drop V2 database or remove generated PDFs during incident response unless separately approved.

