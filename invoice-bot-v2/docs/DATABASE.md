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
