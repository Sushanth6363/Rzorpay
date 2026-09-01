-- Unified Recovery Engine — SQLite DDL Schema (WAL Mode Baseline)
-- Enforces mandatory database-level constraints, composite keys, and atomic budget invariants.

PRAGMA foreign_keys = ON;

-- 1. Ingested Events (Deduplicated via merchant_id + idempotency_key)
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (merchant_id, event_id),
    UNIQUE (merchant_id, idempotency_key)
);

-- 2. Recovery Opportunities (Monetary amounts strictly integer paise)
CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    amount_paise INTEGER NOT NULL CHECK (amount_paise >= 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL,
    source TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (merchant_id, opportunity_id),
    UNIQUE (merchant_id, source_event_id)
);

-- 3. Customer Contact Budgets & Reservation Counters
-- HARD INVARIANT (ADR-0003): reserved_count + consumed_count <= cap
CREATE TABLE IF NOT EXISTS contact_budgets (
    merchant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    cap INTEGER NOT NULL DEFAULT 3 CHECK (cap >= 0),
    reserved_count INTEGER NOT NULL DEFAULT 0 CHECK (reserved_count >= 0),
    consumed_count INTEGER NOT NULL DEFAULT 0 CHECK (consumed_count >= 0),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (merchant_id, customer_id),
    CONSTRAINT chk_contact_cap_limit CHECK (reserved_count + consumed_count <= cap)
);

-- 4. Audit Log
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details_json TEXT,
    timestamp TEXT NOT NULL
);

-- Performance Indices
CREATE INDEX IF NOT EXISTS idx_opportunities_merchant_customer ON opportunities(merchant_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_events_merchant_idempotency ON events(merchant_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_budgets_merchant_customer ON contact_budgets(merchant_id, customer_id);
