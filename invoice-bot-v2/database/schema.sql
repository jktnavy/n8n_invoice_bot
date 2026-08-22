CREATE DATABASE IF NOT EXISTS invoice_bot_v2
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE invoice_bot_v2;

CREATE TABLE customers (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,
  phone VARCHAR(50) NULL,
  email VARCHAR(255) NULL,
  address TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_customers_normalized_name (normalized_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice_drafts (
  id CHAR(36) PRIMARY KEY,
  telegram_chat_id VARCHAR(64) NOT NULL,
  telegram_user_id VARCHAR(64) NULL,
  customer_name VARCHAR(255) NOT NULL,
  payment_type ENUM('FULL_PAYMENT','DOWN_PAYMENT','BALANCE_PAYMENT','UNSPECIFIED') NOT NULL DEFAULT 'UNSPECIFIED',
  subtotal DECIMAL(19,2) NOT NULL DEFAULT 0,
  discount DECIMAL(19,2) NOT NULL DEFAULT 0,
  additional_fee DECIMAL(19,2) NOT NULL DEFAULT 0,
  grand_total DECIMAL(19,2) NOT NULL DEFAULT 0,
  included_text TEXT NULL,
  excluded_text TEXT NULL,
  notes TEXT NULL,
  raw_input TEXT NULL,
  parsed_payload JSON NULL,
  content_fingerprint CHAR(64) NOT NULL,
  status ENUM('DRAFT','AWAITING_APPROVAL','APPROVED','CANCELLED','EXPIRED') NOT NULL DEFAULT 'DRAFT',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NULL,
  KEY idx_drafts_chat_status (telegram_chat_id, status),
  KEY idx_drafts_fingerprint (content_fingerprint)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice_draft_items (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  draft_id CHAR(36) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  trip_date DATE NULL,
  vehicle_type VARCHAR(100) NULL,
  quantity DECIMAL(12,2) NOT NULL DEFAULT 1,
  uom VARCHAR(20) NOT NULL DEFAULT 'Unit',
  pickup VARCHAR(500) NULL,
  destination VARCHAR(500) NULL,
  unit_price DECIMAL(19,2) NOT NULL DEFAULT 0,
  line_total DECIMAL(19,2) NOT NULL DEFAULT 0,
  description VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_draft_items_draft FOREIGN KEY (draft_id)
    REFERENCES invoice_drafts(id) ON DELETE CASCADE,
  KEY idx_draft_items_draft (draft_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice_sequences (
  company_code VARCHAR(10) NOT NULL,
  sequence_year INT NOT NULL,
  last_number INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (company_code, sequence_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoices (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  invoice_number VARCHAR(50) NOT NULL,
  customer_id BIGINT UNSIGNED NULL,
  customer_name VARCHAR(255) NOT NULL,
  invoice_date DATE NOT NULL,
  payment_type ENUM('FULL_PAYMENT','DOWN_PAYMENT','BALANCE_PAYMENT','UNSPECIFIED') NOT NULL,
  subtotal DECIMAL(19,2) NOT NULL DEFAULT 0,
  discount DECIMAL(19,2) NOT NULL DEFAULT 0,
  additional_fee DECIMAL(19,2) NOT NULL DEFAULT 0,
  grand_total DECIMAL(19,2) NOT NULL DEFAULT 0,
  included_text TEXT NULL,
  excluded_text TEXT NULL,
  notes TEXT NULL,
  status ENUM('APPROVED','GENERATING','GENERATED','DELIVERY_PENDING','SENT','GENERATION_FAILED','DELIVERY_FAILED','VOID') NOT NULL DEFAULT 'APPROVED',
  source_draft_id CHAR(36) NULL,
  content_fingerprint CHAR(64) NOT NULL,
  pdf_path VARCHAR(500) NULL,
  pdf_sha256 CHAR(64) NULL,
  pdf_size BIGINT UNSIGNED NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_invoices_invoice_number (invoice_number),
  KEY idx_invoices_customer (customer_name),
  KEY idx_invoices_fingerprint (content_fingerprint),
  KEY idx_invoices_source_draft (source_draft_id),
  CONSTRAINT fk_invoices_customer FOREIGN KEY (customer_id)
    REFERENCES customers(id) ON DELETE SET NULL,
  CONSTRAINT fk_invoices_source_draft FOREIGN KEY (source_draft_id)
    REFERENCES invoice_drafts(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice_items (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  invoice_id BIGINT UNSIGNED NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  trip_date DATE NULL,
  vehicle_type VARCHAR(100) NULL,
  quantity DECIMAL(12,2) NOT NULL DEFAULT 1,
  uom VARCHAR(20) NOT NULL DEFAULT 'Unit',
  pickup VARCHAR(500) NULL,
  destination VARCHAR(500) NULL,
  unit_price DECIMAL(19,2) NOT NULL DEFAULT 0,
  line_total DECIMAL(19,2) NOT NULL DEFAULT 0,
  description VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_invoice_items_invoice FOREIGN KEY (invoice_id)
    REFERENCES invoices(id) ON DELETE CASCADE,
  KEY idx_invoice_items_invoice (invoice_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE telegram_conversations (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  telegram_chat_id VARCHAR(64) NOT NULL,
  telegram_user_id VARCHAR(64) NULL,
  active_draft_id CHAR(36) NULL,
  last_invoice_id BIGINT UNSIGNED NULL,
  conversation_state ENUM('IDLE','AWAITING_APPROVAL','GENERATING','DELIVERY_PENDING','SENT','ERROR') NOT NULL DEFAULT 'IDLE',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_conversation_chat_user (telegram_chat_id, telegram_user_id),
  CONSTRAINT fk_conversations_active_draft FOREIGN KEY (active_draft_id)
    REFERENCES invoice_drafts(id) ON DELETE SET NULL,
  CONSTRAINT fk_conversations_last_invoice FOREIGN KEY (last_invoice_id)
    REFERENCES invoices(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice_deliveries (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  invoice_id BIGINT UNSIGNED NOT NULL,
  channel ENUM('telegram') NOT NULL DEFAULT 'telegram',
  target_chat_id VARCHAR(128) NOT NULL,
  status ENUM('pending','sending','sent','failed') NOT NULL DEFAULT 'pending',
  attempt_count INT NOT NULL DEFAULT 0,
  provider_message_id VARCHAR(128) NULL,
  http_status INT NULL,
  provider_error_code VARCHAR(100) NULL,
  provider_error_message TEXT NULL,
  provider_response JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP NULL,
  last_attempt_at TIMESTAMP NULL,
  CONSTRAINT fk_deliveries_invoice FOREIGN KEY (invoice_id)
    REFERENCES invoices(id) ON DELETE CASCADE,
  KEY idx_deliveries_invoice (invoice_id),
  KEY idx_deliveries_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  correlation_id CHAR(36) NOT NULL,
  event_type VARCHAR(80) NOT NULL,
  entity_type VARCHAR(80) NULL,
  entity_id VARCHAR(80) NULL,
  telegram_chat_id VARCHAR(64) NULL,
  telegram_user_id VARCHAR(64) NULL,
  workflow_name VARCHAR(120) NULL,
  node_name VARCHAR(120) NULL,
  message TEXT NULL,
  metadata JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_audit_correlation (correlation_id),
  KEY idx_audit_event_type (event_type),
  KEY idx_audit_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
