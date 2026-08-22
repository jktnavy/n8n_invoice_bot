USE invoice_bot_v2;

-- Parameters:
-- :telegram_chat_id, :telegram_user_id, :content_fingerprint

SELECT
  id,
  customer_name,
  status,
  content_fingerprint,
  created_at
FROM invoice_drafts
WHERE telegram_chat_id = :telegram_chat_id
  AND telegram_user_id <=> :telegram_user_id
  AND content_fingerprint = :content_fingerprint
  AND status IN ('DRAFT', 'AWAITING_APPROVAL')
ORDER BY created_at DESC
LIMIT 1;

SELECT
  invoices.id,
  invoices.invoice_number,
  invoices.customer_name,
  invoices.status,
  invoices.grand_total,
  invoices.pdf_path,
  invoices.content_fingerprint,
  invoices.created_at
FROM invoices
JOIN invoice_drafts sd
  ON sd.id = invoices.source_draft_id
WHERE invoices.content_fingerprint = :content_fingerprint
  AND sd.telegram_chat_id = :telegram_chat_id
  AND sd.telegram_user_id <=> :telegram_user_id
  AND invoices.status <> 'VOID'
ORDER BY invoices.created_at DESC
LIMIT 1;
