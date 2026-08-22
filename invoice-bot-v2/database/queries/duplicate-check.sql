USE invoice_bot_v2;

-- Parameters:
-- :telegram_chat_id, :content_fingerprint

SELECT
  id,
  customer_name,
  status,
  content_fingerprint,
  created_at
FROM invoice_drafts
WHERE telegram_chat_id = :telegram_chat_id
  AND content_fingerprint = :content_fingerprint
  AND status IN ('DRAFT', 'AWAITING_APPROVAL')
ORDER BY created_at DESC
LIMIT 1;

SELECT
  id,
  invoice_number,
  customer_name,
  status,
  grand_total,
  pdf_path,
  content_fingerprint,
  created_at
FROM invoices
WHERE content_fingerprint = :content_fingerprint
  AND status <> 'VOID'
ORDER BY created_at DESC
LIMIT 1;

