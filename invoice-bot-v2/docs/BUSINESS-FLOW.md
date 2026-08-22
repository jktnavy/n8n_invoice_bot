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

## Cancel Draft

Cancellation is allowed before approval only. It marks the active draft
`CANCELLED`, clears `telegram_conversations.active_draft_id`, returns the
conversation to `IDLE`, and must not allocate an invoice number.

## Payment

`DOWN_PAYMENT` stores the accepted DP amount and recalculates `balance_due`
from the full invoice total. `FULL_PAYMENT` always has zero balance due. These
amounts are calculated by the deterministic workflow and persisted with the
draft and final invoice.

## Status

Status requests must read stored invoice and latest delivery state. If the user
does not mention an invoice number, the workflow uses the conversation's
`last_invoice_id`. The bot must not guess delivery state from natural language.

The offline workflow simulator in `services/workflow-sim` is an executable contract for these flows. n8n implementation should preserve the same observable behavior.

## Audit Events

Every incoming Telegram message gets a `correlation_id` and writes
`MESSAGE_RECEIVED` plus `INTENT_DETECTED`. Successful create/approve/delivery
flows must record at least `DRAFT_CREATED`, `PREVIEW_SENT`,
`APPROVAL_RECEIVED`, `INVOICE_CREATED`, `PDF_GENERATED`, `DELIVERY_STARTED`,
and `DELIVERY_SENT`. Failures use `ERROR` or the specific failure event, such as
`DELIVERY_FAILED`. Draft cancellation records `DRAFT_CANCELLED`. Resend success
records `INVOICE_RESENT`.
