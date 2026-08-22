USE invoice_bot_v2;

-- Parameters:
-- :telegram_chat_id, :telegram_user_id, :invoice_id, :invoice_number
--
-- Caller may pass :invoice_id or :invoice_number. If both are null, the query
-- falls back to telegram_conversations.last_invoice_id for this chat/user.

SELECT
  i.id AS invoice_id,
  i.invoice_number,
  i.customer_name,
  i.status AS invoice_status,
  i.grand_total,
  i.down_payment_amount,
  i.balance_due,
  i.pdf_path,
  d.id AS delivery_id,
  d.status AS delivery_status,
  d.provider_message_id,
  d.provider_error_message,
  d.sent_at,
  d.last_attempt_at
FROM invoices i
JOIN invoice_drafts sd
  ON sd.id = i.source_draft_id
LEFT JOIN telegram_conversations c
  ON c.last_invoice_id = i.id
LEFT JOIN invoice_deliveries d
  ON d.id = (
    SELECT d2.id
    FROM invoice_deliveries d2
    WHERE d2.invoice_id = i.id
    ORDER BY d2.created_at DESC, d2.id DESC
    LIMIT 1
  )
WHERE (
    (
      :invoice_id IS NOT NULL
      AND i.id = :invoice_id
      AND sd.telegram_chat_id = :telegram_chat_id
      AND sd.telegram_user_id <=> :telegram_user_id
    )
    OR (
      :invoice_number IS NOT NULL
      AND i.invoice_number = :invoice_number
      AND sd.telegram_chat_id = :telegram_chat_id
      AND sd.telegram_user_id <=> :telegram_user_id
    )
    OR (
      :invoice_id IS NULL
      AND :invoice_number IS NULL
      AND c.telegram_chat_id = :telegram_chat_id
      AND c.telegram_user_key = COALESCE(:telegram_user_id, '')
    )
  )
  AND i.status <> 'VOID'
ORDER BY i.created_at DESC
LIMIT 1;
