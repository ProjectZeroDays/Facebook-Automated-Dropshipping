"""migrations/runner.py — ordered, idempotent, tracked in _migrations."""
from __future__ import annotations
import os, sqlite3, glob

def run(db_path="fbm.sqlite"):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS _migrations(name TEXT PRIMARY KEY, applied_at TEXT)")
    applied = {r[0] for r in conn.execute("SELECT name FROM _migrations").fetchall()}
    files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "*.sql")))
    for f in files:
        name = os.path.basename(f)
        if name in applied:
            continue
        with open(f, encoding="utf-8") as fh:
            conn.executescript(fh.read())
        conn.execute("INSERT INTO _migrations(name, applied_at) VALUES(?, datetime('now'))", (name,))
        conn.commit()
        print("applied", name)
    conn.close()


if __name__ == "__main__":
    run()