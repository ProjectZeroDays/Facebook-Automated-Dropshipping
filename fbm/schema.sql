-- 001_core.sql  (idempotent; run by bootstrap)
CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY, name TEXT, email TEXT UNIQUE, plan TEXT DEFAULT 'starter',
  state TEXT DEFAULT 'TN', city TEXT, mode TEXT DEFAULT 'ship', status TEXT DEFAULT 'trialing',
  trial_ends TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, tenant_id TEXT, email TEXT UNIQUE,
  role TEXT DEFAULT 'owner', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS subscriptions(tenant_id TEXT PRIMARY KEY, plan TEXT, amount REAL,
  status TEXT, period_end TEXT, stripe_customer TEXT, stripe_sub TEXT);
CREATE TABLE IF NOT EXISTS flags(scope TEXT PRIMARY KEY, json TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS credits(id INTEGER PRIMARY KEY, tenant_id TEXT, amount REAL DEFAULT 0,
  applied REAL DEFAULT 0, reason TEXT, ref TEXT, expires_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS referrals(id TEXT PRIMARY KEY, code TEXT, referrer_tenant TEXT,
  referred_tenant TEXT, reward_amount REAL, status TEXT DEFAULT 'pending',
  referee_credited_at TEXT, referrer_credited_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS affiliates(code TEXT PRIMARY KEY, tenant_id TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS secrets(tenant_id TEXT, name TEXT, value TEXT, PRIMARY KEY(tenant_id,name));
CREATE TABLE IF NOT EXISTS integrations(tenant_id TEXT, iid TEXT, connected INTEGER DEFAULT 0,
  settings TEXT, updated_at TEXT, PRIMARY KEY(tenant_id,iid));
CREATE TABLE IF NOT EXISTS business(tenant_id TEXT PRIMARY KEY, name TEXT, phone TEXT, email TEXT,
  city TEXT, state TEXT, hours TEXT, policies TEXT, return_days INTEGER DEFAULT 30,
  returns_allowed INTEGER DEFAULT 1, shipping_payer TEXT DEFAULT 'fb', free_shipping_over REAL,
  handling_days INTEGER DEFAULT 1, logo TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS bot_rules(tenant_id TEXT PRIMARY KEY, json TEXT);
CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY, thread_id TEXT, text TEXT, confidence REAL,
  status TEXT, tenant_id TEXT NOT NULL DEFAULT 'default', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS threads(id TEXT PRIMARY KEY, title TEXT, last_msg TEXT, intent TEXT,
  replied_at TEXT, seen_at TEXT DEFAULT CURRENT_TIMESTAMP, tenant_id TEXT NOT NULL DEFAULT 'default');
CREATE TABLE IF NOT EXISTS chat_sessions(id TEXT PRIMARY KEY, tenant_id TEXT, title TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS chat_messages(id INTEGER PRIMARY KEY, session_id TEXT, role TEXT,
  text TEXT, attachments TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE VIRTUAL TABLE IF NOT EXISTS chat_fts USING fts5(text, session_id UNINDEXED);
-- business tables (multi-tenant, row-level isolation enforced at the query layer)
CREATE TABLE IF NOT EXISTS skus(sku TEXT PRIMARY KEY, title TEXT, price REAL, cost REAL, category TEXT,
  source TEXT, backup_source TEXT, active INTEGER DEFAULT 1, photos TEXT,
  tenant_id TEXT NOT NULL DEFAULT 'default');
CREATE TABLE IF NOT EXISTS orders(fingerprint TEXT PRIMARY KEY, account TEXT, sku TEXT, title TEXT,
  price REAL, buyer TEXT, address TEXT, status TEXT DEFAULT 'NEW', tracking TEXT, supplier TEXT,
  payload TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT,
  tenant_id TEXT NOT NULL DEFAULT 'default');
CREATE TABLE IF NOT EXISTS samples(sku TEXT PRIMARY KEY, supplier TEXT, ordered_at TEXT, cost REAL,
  latency_days REAL, verdict TEXT, tenant_id TEXT NOT NULL DEFAULT 'default');
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, ref TEXT,
  detail TEXT, account TEXT, tenant_id TEXT NOT NULL DEFAULT 'default',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pnl(id INTEGER PRIMARY KEY AUTOINCREMENT, month TEXT, revenue REAL,
  fees REAL, cogs REAL, refunds REAL, net REAL, orders INTEGER,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS listings(id TEXT PRIMARY KEY, account TEXT, sku TEXT, query TEXT,
  title TEXT, price REAL, location TEXT, url TEXT, variant INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
  renewed INTEGER DEFAULT 0, posted_at TEXT, seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
  tenant_id TEXT NOT NULL DEFAULT 'default');
CREATE TABLE IF NOT EXISTS comps(id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, title TEXT,
  price REAL, location TEXT, url TEXT, account TEXT, seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
  tenant_id TEXT NOT NULL DEFAULT 'default');
