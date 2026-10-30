"""
fbm/interventions.py — nudge log + attribution.
"""
from __future__ import annotations
from fbm import core as C


def log(tenant_id, action, kind="nudge"):
    with C.db() as c:
        c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES(?,?,?,?)",
                  (kind, action, action, tenant_id))
    return True


def main():
    C.load_env()
    print("interventions ok")


if __name__ == "__main__":
    main()