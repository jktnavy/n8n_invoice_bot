USE invoice_bot_v2;

-- Parameters:
-- :correlation_id, :event_type, :entity_type, :entity_id,
-- :telegram_chat_id, :telegram_user_id, :workflow_name, :node_name,
-- :message, :metadata

INSERT INTO audit_logs (
  correlation_id,
  event_type,
  entity_type,
  entity_id,
  telegram_chat_id,
  telegram_user_id,
  workflow_name,
  node_name,
  message,
  metadata
) VALUES (
  :correlation_id,
  :event_type,
  :entity_type,
  :entity_id,
  :telegram_chat_id,
  :telegram_user_id,
  :workflow_name,
  :node_name,
  :message,
  :metadata
);
