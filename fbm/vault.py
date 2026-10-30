"""
fbm/vault.py — per-tenant Fernet-encrypted secret storage.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from cryptography.fernet import Fernet
from fbm import core as C


def _key():
    if os.getenv("VAULT_KEY"): return os.environ["VAULT_KEY"].encode()
    p = Path("data/vault.key")
    if p.exists(): return p.read_bytes().strip()
    p.parent.mkdir(parents=True, exist_ok=True)
    k = Fernet.generate_key(); p.write_bytes(k); os.chmod(p, 0o600); return k


def put(tenant_id, name, value):
    tok = Fernet(_key()).encrypt(json.dumps(value).encode()).decode()
    with C.db() as c:
        c.execute("INSERT INTO secrets(tenant_id,name,value) VALUES(?,?,?) "
                  "ON CONFLICT(tenant_id,name) DO UPDATE SET value=excluded.value",
                  (tenant_id, name, tok))


def get(tenant_id, name):
    with C.db() as c:
        r = c.execute("SELECT value FROM secrets WHERE tenant_id=? AND name=?", (tenant_id, name)).fetchone()
    return json.loads(Fernet(_key()).decrypt(r["value"].encode())) if r else None


def names(tenant_id):
    with C.db() as c:
        return [x["name"] for x in c.execute("SELECT name FROM secrets WHERE tenant_id=?", (tenant_id,))]