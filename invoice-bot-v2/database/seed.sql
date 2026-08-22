USE invoice_bot_v2;

INSERT INTO invoice_sequences (company_code, sequence_year, last_number)
VALUES ('STA', 2026, 0)
ON DUPLICATE KEY UPDATE last_number = last_number;

