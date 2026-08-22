USE invoice_bot_v2;

-- Parameters:
-- :invoice_id, :pdf_path, :pdf_sha256, :pdf_size, :render_succeeded

UPDATE invoices
SET status = CASE
      WHEN :render_succeeded = TRUE THEN 'GENERATED'
      ELSE 'GENERATION_FAILED'
    END,
    pdf_path = CASE WHEN :render_succeeded = TRUE THEN :pdf_path ELSE pdf_path END,
    pdf_sha256 = CASE WHEN :render_succeeded = TRUE THEN :pdf_sha256 ELSE pdf_sha256 END,
    pdf_size = CASE WHEN :render_succeeded = TRUE THEN :pdf_size ELSE pdf_size END
WHERE id = :invoice_id
  AND status IN ('APPROVED', 'GENERATING', 'GENERATION_FAILED')
  AND (
    :render_succeeded = FALSE
    OR (
      :pdf_path IS NOT NULL
      AND :pdf_sha256 REGEXP '^[a-f0-9]{64}$'
      AND :pdf_size > 0
    )
  );
