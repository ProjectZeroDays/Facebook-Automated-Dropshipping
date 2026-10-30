-- 002_auth.sql  passkeys/totp/resets — inline ALTERs
ALTER TABLE users ADD COLUMN password_hash TEXT;
ALTER TABLE users ADD COLUMN password_salt TEXT;
ALTER TABLE users ADD COLUMN totp_secret TEXT;
ALTER TABLE users ADD COLUMN recovery_hashes TEXT;
CREATE TABLE IF NOT EXISTS resets(token TEXT PRIMARY KEY, user_id TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);