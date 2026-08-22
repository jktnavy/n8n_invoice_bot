-- ============================================================
-- Schema MySQL — Otomasi Invoice Telegram STA Transport
-- DB: invoice_bot
-- Tanggal: 14 Agustus 2026
-- Catatan: jalankan dengan user yang punya hak CREATE DATABASE.
-- ============================================================

CREATE DATABASE IF NOT EXISTS invoice_bot
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE invoice_bot;

-- ------------------------------------------------------------
-- Tabel: invoices (header invoice)
-- ------------------------------------------------------------
CREATE TABLE invoices (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  invoice_number  VARCHAR(50)   NOT NULL UNIQUE,
  customer_name   VARCHAR(255)  NOT NULL,
  invoice_date    DATE          NOT NULL,
  payment_type    VARCHAR(100)  NULL,
  dp              TINYINT(1)    NOT NULL DEFAULT 0,
  sub_total       DECIMAL(19,2) NOT NULL DEFAULT 0,
  discount_total  DECIMAL(19,2) NOT NULL DEFAULT 0,
  tax_total       DECIMAL(19,2) NOT NULL DEFAULT 0,
  grand_total     DECIMAL(19,2) NOT NULL DEFAULT 0,
  terbilang       VARCHAR(500)  NULL,
  included_text   TEXT          NULL,
  excluded_text   TEXT          NULL,
  status          ENUM('draft','approved','sent','paid','void')
                  NOT NULL DEFAULT 'draft',
  pdf_path        VARCHAR(500)  NULL,
  source_chat     VARCHAR(255)  NULL,
  raw_request     TEXT          NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_invoices_date (invoice_date),
  INDEX idx_invoices_customer (customer_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabel: invoice_items (rincian perjalanan / baris item)
-- ------------------------------------------------------------
CREATE TABLE invoice_items (
  id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  invoice_id     BIGINT UNSIGNED NOT NULL,
  sort_order     INT NOT NULL DEFAULT 0,
  description    VARCHAR(500)  NULL,
  trip_date      DATE          NULL,
  vehicle_type   VARCHAR(100)  NULL,
  qty            DECIMAL(12,2) NOT NULL DEFAULT 1,
  uom            VARCHAR(20)   NOT NULL DEFAULT 'Unit',
  pickup_address VARCHAR(500)  NULL,
  destination    VARCHAR(500)  NULL,
  price          DECIMAL(19,2) NOT NULL DEFAULT 0,
  line_total     DECIMAL(19,2) NOT NULL DEFAULT 0,
  CONSTRAINT fk_items_invoice FOREIGN KEY (invoice_id)
    REFERENCES invoices(id) ON DELETE CASCADE,
  INDEX idx_items_invoice (invoice_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
