USE invoice_bot_v2;

-- Parameters:
-- :invoice_id optional explicit invoice id
-- :invoice_number optional explicit invoice number
-- :telegram_chat_id required when resolving conversation last invoice
-- :telegram_user_id optional Telegram user id

START TRANSACTION;

SELECT i.id
INTO @invoice_id
FROM invoices i
LEFT JOIN telegram_conversations c ON c.last_invoice_id = i.id
WHERE (
    (:invoice_id IS NOT NULL AND i.id = :invoice_id)
    OR (:invoice_number IS NOT NULL AND i.invoice_number = :invoice_number)
    OR (
      :invoice_id IS NULL
      AND :invoice_number IS NULL
      AND c.telegram_chat_id = :telegram_chat_id
      AND (c.telegram_user_id = :telegram_user_id OR :telegram_user_id IS NULL)
    )
  )
  AND i.status <> 'VOID'
ORDER BY i.created_at DESC
LIMIT 1
FOR UPDATE;

UPDATE invoices
SET status = 'VOID'
WHERE id = @invoice_id
  AND status <> 'VOID';

UPDATE telegram_conversations
SET conversation_state = 'IDLE'
WHERE last_invoice_id = @invoice_id
  AND telegram_chat_id = :telegram_chat_id
  AND (telegram_user_id = :telegram_user_id OR :telegram_user_id IS NULL);

COMMIT;

SELECT @invoice_id AS invoice_id;
