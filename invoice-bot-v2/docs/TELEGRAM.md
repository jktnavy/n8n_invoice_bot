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
