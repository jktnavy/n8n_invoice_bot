# Business Flow

## Create Draft

```text
Telegram message
-> classify intent
-> extract invoice draft
-> validate schema
-> validate business fields
-> calculate totals
-> calculate payment balance
-> fingerprint content
-> check duplicate
-> save draft
-> set active draft
-> send preview
-> wait for approval
```

## Approve Draft

```text
approval message
-> load active draft
-> verify AWAITING_APPROVAL
-> allocate invoice number in transaction
-> create invoice and items
-> render PDF
-> create delivery attempt
-> send Telegram document
-> store provider message id
```

## Revision

Revisions update the active draft only. They must recalculate totals and send a new preview. They must not create final invoices.

## Payment

`DOWN_PAYMENT` stores the accepted DP amount and recalculates `balance_due`
from the full invoice total. `FULL_PAYMENT` always has zero balance due. These
amounts are calculated by the deterministic workflow and persisted with the
draft and final invoice.

The offline workflow simulator in `services/workflow-sim` is an executable contract for these flows. n8n implementation should preserve the same observable behavior.
