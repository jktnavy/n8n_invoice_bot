# Architecture

V2 is a greenfield system isolated from the legacy Hermes bot.

```text
Telegram -> n8n -> LLM structured output -> n8n deterministic workflow -> MySQL -> renderer -> Telegram
```

Responsibilities:

- LLM: intent classification and structured extraction only.
- n8n: orchestration, validation, calculation, state transition, duplicate handling, retry.
- MySQL: source of truth for drafts, invoices, sequences, conversations, deliveries, and audit logs.
- Invoice renderer: validated payload to PDF.
- Telegram API: delivery result source of truth.

The renderer receives a full validated invoice payload and does not read MySQL directly.

Audit logging is part of orchestration, not rendering. n8n/backend code carries
one `correlation_id` from Telegram through LLM, database, renderer, and
delivery, then writes sanitized events to `audit_logs`.
