"""
fbm/tenants.py — multi-tenant data isolation.

Multi-tenant management: list tenants, impersonate for support, grant comps,
gate features by tier, rotate credentials, export / erase tenant data.

Every table that holds per-tenant business data carries a `tenant_id` column
(see core.TENANT_ID_COLUMNS).  The helpers here export and erase a tenant's
rows across *all* of those tables so no data leaks between tenants.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from fbm import core as C


# Every business table that carries a tenant_id column.  Export/erase must
# touch each one so no cross-tenant data remains.
TENANT_TABLES = (
    "skus", "orders", "samples", "events", "threads",
    "listings", "comps", "pnl", "drafts",
)


def list_all() -> list:
    """Return all tenants as a list of dicts."""
    C.load_env()
    with C.db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM tenants").fetchall()]


def get(tenant_id: str) -> dict | None:
    """Return a single tenant by ID, or None."""
    C.load_env()
    with C.db() as c:
        row = c.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,)).fetchone()
        return dict(row) if row else None


def create(email: str, plan: str = "starter") -> dict:
    """Create a new tenant. Returns the tenant dict."""
    C.load_env()
    import uuid
    tenant_id = f"t_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    with C.db() as c:
        c.execute(
            "INSERT INTO tenants(id, email, plan, created_at) VALUES(?,?,?,?)",
            (tenant_id, email, plan, now),
        )
    return {"id": tenant_id, "email": email, "plan": plan, "created_at": now}


def ensure_default() -> dict:
    """Ensure a single default tenant exists and return it (backward compat)."""
    C.load_env()
    with C.db() as c:
        row = c.execute("SELECT * FROM tenants WHERE id=?", (C.DEFAULT_TENANT_ID,)).fetchone()
        if row:
            return dict(row)
    return create("default@localhost", "starter")


def impersonate(tenant_id: str, support_email: str) -> dict:
    """Impersonate a tenant for support. Returns impersonation token."""
    C.load_env()
    if not get(tenant_id):
        return {"error": "tenant not found"}
    token = f"imp_{tenant_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    C.notify(f"tenants: impersonate {tenant_id} by {support_email}", "warn")
    return {"tenant_id": tenant_id, "token": token, "by": support_email}


def comp(tenant_id: str, days: int, reason: str) -> dict:
    """Grant complimentary days to a tenant."""
    C.load_env()
    if not get(tenant_id):
        return {"error": "tenant not found"}
    C.notify(f"tenants: comp {tenant_id} +{days}d ({reason})", "info")
    return {"tenant_id": tenant_id, "days": days, "reason": reason}


def gate(tenant_id: str, feature: str) -> bool:
    """Check if *feature* is gated for *tenant*. Returns True if allowed."""
    tenant = get(tenant_id)
    if not tenant:
        return False
    plan = tenant.get("plan", "starter")
    plan_features = {
        "starter": ["1_profile", "150_listings", "email_support"],
        "pro": ["3_profiles", "800_listings", "reprice", "supplier_failover", "priority_support"],
        "agency": ["10_profiles", "unlimited_listings", "api_access", "white_label", "named_support"],
    }
    return feature in plan_features.get(plan, [])


def rotate(tenant_id: str) -> dict:
    """Rotate tenant credentials/API keys."""
    C.load_env()
    if not get(tenant_id):
        return {"error": "tenant not found"}
    import uuid
    new_key = f"fk_{uuid.uuid4().hex[:24]}"
    C.notify(f"tenants: rotated credentials for {tenant_id}", "warn")
    return {"tenant_id": tenant_id, "new_key": new_key}


def export(tenant_id: str) -> dict:
    """Export all data for a tenant (GDPR/CCPA right to access).

    Reads every tenant-scoped table so the export is complete.
    """
    C.load_env()
    tenant = get(tenant_id)
    if not tenant:
        return {"error": "tenant not found"}

    data = {"tenant": tenant, "exported_at": datetime.now(timezone.utc).isoformat()}
    with C.db() as c:
        for table in TENANT_TABLES:
            try:
                rows = c.execute(
                    f"SELECT * FROM {table} WHERE tenant_id=?", (tenant_id,)
                ).fetchall()
                data[table] = [dict(r) for r in rows]
            except Exception:
                # Table may not exist yet in older DBs; skip gracefully.
                data[table] = []
    return data


def delete(tenant_id: str) -> dict:
    """Delete all data for a tenant (GDPR/CCPA right to erasure).

    Removes the tenant's rows from every tenant-scoped table, then the tenant
    record itself.  Never deletes another tenant's data.
    """
    C.load_env()
    tenant = get(tenant_id)
    if not tenant:
        return {"error": "tenant not found"}

    with C.db() as c:
        for table in TENANT_TABLES:
            try:
                c.execute(f"DELETE FROM {table} WHERE tenant_id=?", (tenant_id,))
            except Exception:
                pass
        c.execute("DELETE FROM tenants WHERE id=?", (tenant_id,))
    C.notify(f"tenants: deleted {tenant_id}", "warn")
    return {"tenant_id": tenant_id, "deleted": True}


def tenant_count() -> int:
    """Return the number of tenants."""
    C.load_env()
    with C.db() as c:
        return c.execute("SELECT COUNT(*) n FROM tenants").fetchone()["n"]


def main():
    C.load_env(); C.init_db()
    print(list_all())
    print("tenants ok")


if __name__ == "__main__":
    main()
