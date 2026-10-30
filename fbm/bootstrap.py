"""
fbm/bootstrap.py — idempotent first-run setup.
"""
from __future__ import annotations
import csv, os
from pathlib import Path
from fbm import core as C, accounts, validate


def main(tenant_id=C.DEFAULT_TENANT_ID):
    C.load_env(); C.init_db()
    # 1. accounts
    for name in (os.getenv("ACCOUNTS", "main").split(",")):
        accounts.add(name.strip(), os.getenv("CITY", "memphis"), 10)
    # 2. skus from inventory.csv
    inv = Path("inventory.csv")
    if inv.exists():
        rows = list(csv.DictReader(inv.open(newline="", encoding="utf-8")))
        with C.db() as c:
            for r in rows:
                c.execute("INSERT OR REPLACE INTO skus(sku,title,price,cost,category,source,"
                          "backup_source,photos,active,tenant_id) VALUES(?,?,?,?,?,?,?,?,1,?)",
                          (r["sku"], r["title"], float(r["price"]), float(r.get("cost") or 0),
                           r.get("category",""), r.get("source",""), r.get("backup_source",""),
                           r.get("photos",""), tenant_id))
        print(f"seeded {len(rows)} SKUs for tenant {tenant_id}")
    # 3. selectors
    if not C.SEL_PATH.exists():
        C.SEL_PATH.write_text("{}")
    # 4. validate copy
    if inv.exists():
        validate.main()
    # 5. report
    with C.db() as c:
        n = c.execute("SELECT COUNT(*) n FROM skus WHERE active=1 AND tenant_id=?",
                      (tenant_id,)).fetchone()["n"]
    print(f"ready: {n} active SKUs, {len(accounts.active())} accounts for tenant {tenant_id}")
    print("next: python -m fbm.login_once --calibrate  ->  docker compose up -d")


if __name__ == "__main__":
    main()