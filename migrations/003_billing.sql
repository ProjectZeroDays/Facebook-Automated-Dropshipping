-- 003_billing.sql  subs/credits/referrals/webhooks — inline
CREATE TABLE IF NOT EXISTS subscriptions(
    tenant_id TEXT PRIMARY KEY, plan TEXT, amount REAL, status TEXT,
    period_end TEXT, stripe_customer TEXT, stripe_sub TEXT);
CREATE TABLE IF NOT EXISTS usage(
    tenant_id TEXT, period TEXT, metric TEXT, value REAL,
    PRIMARY KEY(tenant_id, period, metric));
CREATE TABLE IF NOT EXISTS gmv_ledger(
    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT, order_fp TEXT, amount REAL,
    fee REAL, period TEXT, settled INTEGER DEFAULT 0);