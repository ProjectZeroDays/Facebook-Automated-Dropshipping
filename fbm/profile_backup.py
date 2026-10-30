"""
fbm/profile_backup.py — encrypted profile + DB backup so redeploys need no login.

  python -m fbm.profile_backup backup      # -> data/backups/fbm_YYYYmmdd.tar.gz.enc
  python -m fbm.profile_backup restore
  python -m fbm.profile_backup verify      # test-restore the latest backup
"""
from __future__ import annotations
import os, sqlite3, subprocess, sys, tarfile, tempfile
from datetime import datetime
from pathlib import Path
from fbm import core as C
from fbm.observability import integrity_check, get_logger

BK = Path("data/backups")
log = get_logger("backup")


def backup():
    BK.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    raw = BK / f"fbm_{ts}.tar.gz"
    with tarfile.open(raw, "w:gz") as t:
        for p in (C.PROFILE_DIR, os.getenv("FBM_DB", "fbm.sqlite"), "data/selectors.json"):
            if Path(p).exists(): t.add(p)
    pw = os.getenv("BACKUP_PASSWORD", "changeme")
    enc = raw.with_suffix(".gz.enc")
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt",
                    "-in", str(raw), "-out", str(enc), "-pass", f"pass:{pw}"], check=True)
    raw.unlink()
    keep = int(os.getenv("BACKUP_KEEP", "7"))
    for old in sorted(BK.glob("fbm_*.enc"))[:-keep]:
        old.unlink()
    C.notify(f"backup written {enc.name}")
    print(enc)


def restore(path=None):
    files = sorted(BK.glob("fbm_*.enc"))
    src = Path(path) if path else (files[-1] if files else None)
    if not src: raise SystemExit("no backup found")
    pw = os.getenv("BACKUP_PASSWORD", "changeme")
    out = BK / "restore.tar.gz"
    subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
                    "-in", str(src), "-out", str(out), "-pass", f"pass:{pw}"], check=True)
    with tarfile.open(out) as t: t.extractall(".")
    print(f"restored {src.name}")


def verify_backup(path=None) -> dict:
    """Test-restore a backup to a temp dir and verify the DB is intact.

    Returns a report dict: {"ok": bool, "db": path|None, "tables": [...],
    "integrity": bool, "error": str|None}. Never raises.
    """
    report: dict = {"ok": False, "db": None, "tables": [], "integrity": False, "error": None}
    files = sorted(BK.glob("fbm_*.enc"))
    src = Path(path) if path else (files[-1] if files else None)
    if not src:
        report["error"] = "no backup found"
        log.warning("backup verification skipped", extra={"event": "backup.verify", "ok": False, "reason": "no_backup"})
        return report

    tmp = Path(tempfile.mkdtemp(prefix="fbm_verify_"))
    dec = tmp / "restore.tar.gz"
    pw = os.getenv("BACKUP_PASSWORD", "changeme")
    try:
        subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
             "-in", str(src), "-out", str(dec), "-pass", f"pass:{pw}"],
            check=True, capture_output=True,
        )
        with tarfile.open(dec) as t:
            t.extractall(tmp)
        # locate the sqlite db inside the extracted backup
        db_files = list(tmp.rglob("*.sqlite")) + list(tmp.rglob("*.sqlite3")) + list(tmp.rglob("fbm.sqlite"))
        if not db_files:
            report["error"] = "no sqlite database in backup"
            log.warning("backup verification failed",
                        extra={"event": "backup.verify", "ok": False, "reason": "no_db", "backup": src.name})
            return report
        db = db_files[0]
        report["db"] = str(db)
        conn = sqlite3.connect(str(db))
        try:
            report["integrity"] = integrity_check(conn)
            report["tables"] = [
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
            ]
            conn.close()
        except sqlite3.DatabaseError as exc:
            report["error"] = str(exc)
            try:
                conn.close()
            except Exception:
                pass
            log.error("backup verification failed",
                      extra={"event": "backup.verify", "ok": False, "reason": "db_error", "backup": src.name})
            return report
        report["ok"] = bool(report["integrity"] and report["tables"])
        log.info("backup verification complete",
                 extra={"event": "backup.verify", "ok": report["ok"], "backup": src.name,
                        "tables": report["tables"]})
        return report
    except Exception as exc:  # openssl/tar failure -> verification failed
        report["error"] = str(exc)
        log.error("backup verification failed",
                  extra={"event": "backup.verify", "ok": False, "reason": "extract_error", "backup": src.name})
        return report
    finally:
        # best-effort cleanup of the temp dir
        try:
            for child in tmp.rglob("*"):
                if child.is_file():
                    child.unlink()
            tmp.rmdir()
        except Exception:
            pass


if __name__ == "__main__":
    C.load_env()
    action = sys.argv[1] if len(sys.argv) > 1 else "backup"
    {"backup": backup, "restore": restore, "verify": verify_backup}.get(action, backup)()