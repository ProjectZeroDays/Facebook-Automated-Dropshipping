"""
fbm/accountdata.py — export, selective wipe, delete+grace.
"""
from __future__ import annotations
from fbm import core as C


def export(tenant_id):
    C.load_env()
    with C.db() as c:
        rows = c.execute("SELECT * FROM orders WHERE account=?", (tenant_id,)).fetchall()
    return [dict(r) for r in rows]


def main():
    C.load_env()
    print("accountdata ok")


if __name__ == "__main__":
    main()