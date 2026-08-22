USE invoice_bot_v2;

-- Parameters:
-- :draft_id, :telegram_chat_id, :telegram_user_id, :company_code,
-- :sequence_year, :invoice_number, :invoice_date
--
-- The caller must compute :invoice_number from the allocated sequence:
-- INV-0001/STA/VIII/2026

START TRANSACTION;

SELECT *
FROM invoice_drafts
WHERE id = :draft_id
  AND telegram_chat_id = :telegram_chat_id
  AND status = 'AWAITING_APPROVAL'
FOR UPDATE;

INSERT INTO invoice_sequences (company_code, sequence_year, last_number)
VALUES (:company_code, :sequence_year, 0)
ON DUPLICATE KEY UPDATE last_number = last_number;

SELECT last_number
FROM invoice_sequences
WHERE company_code = :company_code
  AND sequence_year = :sequence_year
FOR UPDATE;

UPDATE invoice_sequences
SET last_number = last_number + 1
WHERE company_code = :company_code
  AND sequence_year = :sequence_year;

INSERT INTO customers (name, normalized_name)
SELECT d.customer_name, LOWER(TRIM(d.customer_name))
FROM invoice_drafts d
WHERE d.id = :draft_id
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO invoices (
  invoice_number,
  customer_id,
  customer_name,
  invoice_date,
  payment_type,
  subtotal,
  discount,
  additional_fee,
  grand_total,
  included_text,
  excluded_text,
  notes,
  status,
  source_draft_id,
  content_fingerprint
)
SELECT
  :invoice_number,
  c.id,
  d.customer_name,
  :invoice_date,
  d.payment_type,
  d.subtotal,
  d.discount,
  d.additional_fee,
  d.grand_total,
  d.included_text,
  d.excluded_text,
  d.notes,
  'APPROVED',
  d.id,
  d.content_fingerprint
FROM invoice_drafts d
LEFT JOIN customers c ON c.normalized_name = LOWER(TRIM(d.customer_name))
WHERE d.id = :draft_id;

SET @invoice_id = LAST_INSERT_ID();

INSERT INTO invoice_items (
  invoice_id,
  sort_order,
  trip_date,
  vehicle_type,
  quantity,
  uom,
  pickup,
  destination,
  unit_price,
  line_total,
  description
)
SELECT
  @invoice_id,
  sort_order,
  trip_date,
  vehicle_type,
  quantity,
  uom,
  pickup,
  destination,
  unit_price,
  line_total,
  description
FROM invoice_draft_items
WHERE draft_id = :draft_id
ORDER BY sort_order;

UPDATE invoice_drafts
SET status = 'APPROVED'
WHERE id = :draft_id;

UPDATE telegram_conversations
SET active_draft_id = NULL,
    last_invoice_id = @invoice_id,
    conversation_state = 'GENERATING'
WHERE telegram_chat_id = :telegram_chat_id
  AND (telegram_user_id = :telegram_user_id OR telegram_user_id IS NULL);

COMMIT;

SELECT @invoice_id AS invoice_id;

