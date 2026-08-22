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

Draft creation updates `telegram_conversations.active_draft_id` only when the
conversation is `IDLE`, already `AWAITING_APPROVAL`, or `ERROR`. It must not
replace a conversation that is currently generating, delivering, or already
sent.

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

`database/seed.sql` initializes the `STA` sequence row for 2026 with
`last_number = 0`. `scripts/migrate.sh` applies both `schema.sql` and
`seed.sql`; `scripts/validate-db.sh` verifies that the sequence seed exists
before reporting `MYSQL_BOOTSTRAP=PASS`.

`invoices.source_draft_id` is unique so the same draft cannot create two final
invoice records. Delivery retry/resend creates a new delivery attempt, not a new
invoice.

Renderer completion uses `database/queries/update-render-result.sql`. The
workflow passes `render_succeeded`; the query derives `GENERATED` or
`GENERATION_FAILED` and only stores PDF metadata when the render succeeded with
a non-empty path, 64-character lowercase SHA-256, and positive file size.

Telegram delivery completion uses `database/queries/update-delivery-result.sql`.
The query increments `attempt_count` in the database, accepts only `sent` or
`failed`, requires `provider_message_id` for successful sends, and derives the
invoice status from the stored delivery result.

`telegram_conversations` uses a generated `telegram_user_key` based on
`COALESCE(telegram_user_id, '')` for the unique chat/user key. This prevents
duplicate conversation rows when Telegram user id is unavailable and would
otherwise be stored as `NULL`.
Conversation lookup queries use the same generated key instead of `OR
telegram_user_id IS NULL` matching.

Duplicate and status/detail lookups are scoped to the source draft chat/user.
Explicit `invoice_id` or `invoice_number` lookup still requires the invoice to
come from the same Telegram chat/user that created the source draft.

Final invoice cancellation uses `database/queries/void-invoice.sql` and updates
`invoices.status` to `VOID` without deleting invoices, items, PDFs, deliveries,
or audit records. Voided invoices are ignored by duplicate and status lookup
queries. The query initializes its selected invoice id before lookup and only
updates records when a matching invoice is found.

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
