# Business Flow

## Create Draft

```text
Telegram message
-> classify intent
-> extract invoice draft
-> validate schema
-> validate business fields
-> calculate totals
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

The offline workflow simulator in `services/workflow-sim` is an executable contract for these flows. n8n implementation should preserve the same observable behavior.
