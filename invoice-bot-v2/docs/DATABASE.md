# Database

Database name:

```text
invoice_bot_v2
```

Core tables:

- `customers`
- `invoice_drafts`
- `invoice_draft_items`
- `invoices`
- `invoice_items`
- `invoice_sequences`
- `telegram_conversations`
- `invoice_deliveries`
- `audit_logs`

Invoice number allocation must happen inside a transaction using `invoice_sequences`.

Drafts do not consume final invoice numbers.

Sequence allocation strategy:

```text
START TRANSACTION
INSERT sequence row if missing
SELECT sequence row FOR UPDATE
UPDATE last_number = last_number + 1
INSERT invoice + invoice_items
COMMIT
```

Do not use `SELECT MAX(invoice_number) + 1`.

Runtime DB user should be scoped to `invoice_bot_v2`; see `database/create-runtime-user.example.sql`.
