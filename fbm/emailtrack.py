"""
fbm/emailtrack.py — pixel, click wrap, variant stats.
"""
from __future__ import annotations
from fbm import core as C


def track(event, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES('email_track',?,?,?)",
                  ("email", str(event), tenant_id))
    return True


def main():
    C.load_env()
    print("emailtrack ok")


if __name__ == "__main__":
    main()