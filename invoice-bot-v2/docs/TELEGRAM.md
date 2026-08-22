# Telegram

Normal invoice delivery uses the incoming source chat:

```text
target chat id = Telegram incoming message chat.id
```

No default group fallback is allowed.

Delivery succeeds only when Telegram returns:

```json
{
  "ok": true,
  "result": {
    "message_id": 123
  }
}
```

Store provider errors in `invoice_deliveries` without secrets.

Delivery destination column:

```text
target_chat_id
```

n8n prepares a `sendDocument` payload with:

```text
chat_id
document_path
caption
```

The dependency-free Telegram gateway client in `services/telegram-gateway` maps `sendDocument` responses into DB-ready delivery metadata:

```text
delivery_status
http_status
provider_message_id
provider_error_code
provider_error_message
provider_response
```

It rejects missing `chat_id` before making a request and does not decide retries or create invoices.

Safe operational helpers:

```bash
./scripts/test-telegram.sh
./scripts/telegram-webhook.sh info
./scripts/telegram-webhook.sh set https://example.trycloudflare.com/webhook/telegram/invoice-bot-v2
./scripts/telegram-webhook.sh delete
```

The webhook helper requires the V2 n8n webhook path
`/webhook/telegram/invoice-bot-v2`, limits Telegram updates to `message`, and
asks Telegram to drop pending updates when replacing the webhook.

The bot token is read from `TELEGRAM_BOT_TOKEN`; do not pass it as a CLI argument.
