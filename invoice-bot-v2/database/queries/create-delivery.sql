USE invoice_bot_v2;

-- Parameters:
-- :invoice_id, :target_chat_id

SET @delivery_id = 0;

INSERT INTO invoice_deliveries (
  invoice_id,
  channel,
  target_chat_id,
  status,
  attempt_count
) SELECT
  id,
  'telegram',
  :target_chat_id,
  'pending',
  0
FROM invoices
WHERE id = :invoice_id
  AND status IN ('GENERATED', 'DELIVERY_FAILED', 'SENT')
  AND pdf_path IS NOT NULL
  AND TRIM(pdf_path) <> ''
  AND :target_chat_id IS NOT NULL
  AND TRIM(CAST(:target_chat_id AS CHAR)) <> '';

SET @delivery_id = IF(ROW_COUNT() = 1, LAST_INSERT_ID(), 0);

SELECT @delivery_id AS delivery_id;
