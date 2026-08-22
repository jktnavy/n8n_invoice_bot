USE invoice_bot_v2;

-- Parameters:
-- :invoice_id, :target_chat_id

INSERT INTO invoice_deliveries (
  invoice_id,
  channel,
  target_chat_id,
  status,
  attempt_count
) VALUES (
  :invoice_id,
  'telegram',
  :target_chat_id,
  'pending',
  0
);

SELECT LAST_INSERT_ID() AS delivery_id;

