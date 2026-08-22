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

The dependency-free Telegram gateway client in `services/telegram-gateway` maps `sendDocument` responses into DB-ready delivery metadata:

```text
delivery_status
provider_message_id
provider_error_code
provider_error_message
provider_response
```

It rejects missing `chat_id` before making a request and does not decide retries or create invoices.
