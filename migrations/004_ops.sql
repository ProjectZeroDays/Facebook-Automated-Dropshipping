-- 004_ops.sql  drip/interventions/email_events — inline
CREATE TABLE IF NOT EXISTS email_events(
    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT, slug TEXT, subject TEXT, sent_at TEXT);
CREATE TABLE IF NOT EXISTS webhook_events(
    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT, type TEXT, state TEXT, attempts INTEGER DEFAULT 0,
    received_at TEXT DEFAULT CURRENT_TIMESTAMP);