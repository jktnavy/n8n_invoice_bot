USE invoice_bot_v2;

-- Parameters:
-- :delivery_id, :status, :attempt_count, :provider_message_id,
-- :http_status, :provider_error_code, :provider_error_message,
-- :provider_response

UPDATE invoice_deliveries
SET status = :status,
    attempt_count = :attempt_count,
    provider_message_id = :provider_message_id,
    http_status = :http_status,
    provider_error_code = :provider_error_code,
    provider_error_message = :provider_error_message,
    provider_response = :provider_response,
    sent_at = CASE WHEN :status = 'sent' THEN CURRENT_TIMESTAMP ELSE sent_at END,
    last_attempt_at = CURRENT_TIMESTAMP
WHERE id = :delivery_id;

UPDATE invoices i
JOIN invoice_deliveries d ON d.invoice_id = i.id
SET i.status = CASE WHEN d.status = 'sent' THEN 'SENT' ELSE 'DELIVERY_FAILED' END
WHERE d.id = :delivery_id;
