USE invoice_bot_v2;

-- Parameters expected from n8n:
-- :draft_id, :telegram_chat_id, :telegram_user_id, :customer_name,
-- :payment_type, :subtotal, :discount, :additional_fee, :grand_total,
-- :down_payment_amount, :balance_due,
-- :included_text, :excluded_text, :notes, :raw_input, :parsed_payload,
-- :content_fingerprint, :expires_at

START TRANSACTION;

INSERT INTO invoice_drafts (
  id,
  telegram_chat_id,
  telegram_user_id,
  customer_name,
  payment_type,
  subtotal,
  discount,
  additional_fee,
  grand_total,
  down_payment_amount,
  balance_due,
  included_text,
  excluded_text,
  notes,
  raw_input,
  parsed_payload,
  content_fingerprint,
  status,
  expires_at
) VALUES (
  :draft_id,
  :telegram_chat_id,
  :telegram_user_id,
  :customer_name,
  :payment_type,
  :subtotal,
  :discount,
  :additional_fee,
  :grand_total,
  :down_payment_amount,
  :balance_due,
  :included_text,
  :excluded_text,
  :notes,
  :raw_input,
  :parsed_payload,
  :content_fingerprint,
  'AWAITING_APPROVAL',
  :expires_at
);

-- Insert invoice_draft_items separately as parameterized rows/batches.

INSERT INTO telegram_conversations (
  telegram_chat_id,
  telegram_user_id,
  active_draft_id,
  conversation_state
) VALUES (
  :telegram_chat_id,
  :telegram_user_id,
  :draft_id,
  'AWAITING_APPROVAL'
)
ON DUPLICATE KEY UPDATE
  active_draft_id = VALUES(active_draft_id),
  conversation_state = VALUES(conversation_state);

COMMIT;
