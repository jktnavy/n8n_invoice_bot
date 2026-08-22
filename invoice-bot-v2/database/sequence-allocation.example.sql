USE invoice_bot_v2;

-- Example transaction-safe invoice number allocation.
-- Application/n8n must run this inside the same transaction that creates
-- the approved invoice record.

START TRANSACTION;

INSERT INTO invoice_sequences (company_code, sequence_year, last_number)
VALUES ('STA', 2026, 0)
ON DUPLICATE KEY UPDATE last_number = last_number;

SELECT last_number
FROM invoice_sequences
WHERE company_code = 'STA'
  AND sequence_year = 2026
FOR UPDATE;

UPDATE invoice_sequences
SET last_number = last_number + 1
WHERE company_code = 'STA'
  AND sequence_year = 2026;

SELECT last_number AS allocated_sequence
FROM invoice_sequences
WHERE company_code = 'STA'
  AND sequence_year = 2026;

-- Create invoice + invoice_items here using the allocated sequence.

COMMIT;

