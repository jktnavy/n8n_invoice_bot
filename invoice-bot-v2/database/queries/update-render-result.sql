USE invoice_bot_v2;

-- Parameters:
-- :invoice_id, :pdf_path, :pdf_sha256, :pdf_size, :status

UPDATE invoices
SET status = :status,
    pdf_path = :pdf_path,
    pdf_sha256 = :pdf_sha256,
    pdf_size = :pdf_size
WHERE id = :invoice_id;

