USE invoice_bot_v2;

-- Parameters:
-- :delivery_id, :delivery_status, :provider_message_id,
-- :http_status, :provider_error_code, :provider_error_message,
-- :provider_response

UPDATE invoice_deliveries
SET status = :delivery_status,
    attempt_count = attempt_count + 1,
    provider_message_id = CASE WHEN :delivery_status = 'sent' THEN :provider_message_id ELSE NULL END,
    http_status = :http_status,
    provider_error_code = CASE WHEN :delivery_status = 'failed' THEN :provider_error_code ELSE NULL END,
    provider_error_message = CASE WHEN :delivery_status = 'failed' THEN :provider_error_message ELSE NULL END,
    provider_response = :provider_response,
    sent_at = CASE WHEN :delivery_status = 'sent' THEN CURRENT_TIMESTAMP ELSE sent_at END,
    last_attempt_at = CURRENT_TIMESTAMP
WHERE id = :delivery_id
  AND status IN ('pending', 'sending', 'failed')
  AND :delivery_status IN ('sent', 'failed')
  AND (
    :delivery_status = 'failed'
    OR (
      :provider_message_id IS NOT NULL
      AND TRIM(CAST(:provider_message_id AS CHAR)) <> ''
    )
  );

UPDATE invoices i
JOIN invoice_deliveries d ON d.invoice_id = i.id
SET i.status = CASE WHEN d.status = 'sent' THEN 'SENT' ELSE 'DELIVERY_FAILED' END
WHERE d.id = :delivery_id
  AND d.status IN ('sent', 'failed');
