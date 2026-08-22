-- ============================================================
-- Migration 2026-08-22 — Delivery status & idempotency
-- DB: invoice_bot
-- Menambah kolom untuk audit delivery Telegram + deteksi duplikat.
-- ============================================================
USE invoice_bot;

ALTER TABLE invoices
  ADD COLUMN request_fingerprint VARCHAR(64)  NULL AFTER raw_request,
  ADD COLUMN delivery_status     VARCHAR(20)  NOT NULL DEFAULT 'pending' AFTER status,
  ADD COLUMN telegram_message_id BIGINT       NULL AFTER delivery_status,
  ADD COLUMN telegram_chat_id    VARCHAR(50)  NULL AFTER telegram_message_id,
  ADD COLUMN delivery_error      VARCHAR(500) NULL AFTER telegram_chat_id,
  ADD INDEX idx_invoices_fingerprint (request_fingerprint);

-- Verifikasi
SHOW COLUMNS FROM invoices LIKE '%delivery%';
SHOW COLUMNS FROM invoices LIKE '%telegram%';
SHOW COLUMNS FROM invoices LIKE '%fingerprint%';
