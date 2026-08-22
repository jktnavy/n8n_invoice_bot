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

`invoice_drafts` and `invoices` store deterministic payment amounts:
`down_payment_amount` and `balance_due`. The workflow recalculates these values
from extracted payment intent and grand total before persistence.

Sequence allocation strategy:

```text
START TRANSACTION
INSERT sequence row if missing
SELECT sequence row FOR UPDATE
UPDATE last_number = last_number + 1
SELECT last_number INTO @allocated_sequence
INSERT invoice + invoice_items
COMMIT
```

`database/queries/approve-draft.sql` formats `invoice_number` from
`@allocated_sequence`, company code, roman invoice month, and invoice year
inside the approval transaction. Do not pass a user-provided invoice number
into approval.

`invoices.source_draft_id` is unique so the same draft cannot create two final
invoice records. Delivery retry/resend creates a new delivery attempt, not a new
invoice.

`telegram_conversations` uses a generated `telegram_user_key` based on
`COALESCE(telegram_user_id, '')` for the unique chat/user key. This prevents
duplicate conversation rows when Telegram user id is unavailable and would
otherwise be stored as `NULL`.
Conversation lookup queries use the same generated key instead of `OR
telegram_user_id IS NULL` matching.

Final invoice cancellation uses `database/queries/void-invoice.sql` and updates
`invoices.status` to `VOID` without deleting invoices, items, PDFs, deliveries,
or audit records. Voided invoices are ignored by duplicate and status lookup
queries.

Do not use `SELECT MAX(invoice_number) + 1`.

Runtime DB user should be scoped to `invoice_bot_v2`; see `database/create-runtime-user.example.sql`.

Parameterized operation templates live in `database/queries/`. They are intended to be translated into n8n MySQL nodes or backend code without changing the transaction boundaries.

Validate a real database bootstrap with:

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_DATABASE=invoice_bot_v2
export MYSQL_USER=invoice_bot_v2
read -rsp "MYSQL_PASSWORD: " MYSQL_PASSWORD
export MYSQL_PASSWORD
./scripts/validate-db.sh
```
