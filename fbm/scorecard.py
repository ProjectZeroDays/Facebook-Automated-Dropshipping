"""
fbm/scorecard.py — churn risk.
"""
from __future__ import annotations
from fbm import core as C


def run(tenant_id=C.DEFAULT_TENANT_ID):
    C.load_env()
    with C.db() as c:
        n = c.execute("SELECT COUNT(*) n FROM orders WHERE tenant_id=?", (tenant_id,)).fetchone()["n"]
    return {"orders": n, "risk": "low" if n < 5 else "medium"}


def main():
    C.load_env(); C.init_db()
    print(run())


if __name__ == "__main__":
    main()