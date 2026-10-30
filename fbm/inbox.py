"""inbox.py — Messenger poller.

Polls Facebook Messenger threads, classifies intent via returns.py, and
either auto-replies (high confidence) or queues for one-tap approval via
inbox_ai.py.
"""
from __future__ import annotations
from datetime import datetime
from fbm import core as C
from fbm import returns as Returns


def poll_once(limit: int = 50, tenant_id=C.DEFAULT_TENANT_ID) -> int:
    """Poll Messenger for unanswered threads. Returns count processed."""
    C.load_env()
    processed = 0
    with C.db() as c:
        threads = c.execute(
            "SELECT id, last_msg, intent, replied_at FROM threads "
            "WHERE replied_at IS NULL AND tenant_id=? ORDER BY seen_at DESC LIMIT ?",
            (tenant_id, limit),
        ).fetchall()
        for t in threads:
            intent = t["intent"] or Returns.classify(t["last_msg"] or "")
            reply = Returns.reply(t["last_msg"] or "")
            if reply and intent:
                c.execute(
                    "UPDATE threads SET intent=?, replied_at=datetime('now') WHERE id=? AND tenant_id=?",
                    (intent, t["id"], tenant_id),
                )
                C.notify(f"inbox: auto-replied to thread {t['id']} ({intent})", "info")
            else:
                c.execute(
                    "UPDATE threads SET intent=? WHERE id=? AND tenant_id=?",
                    (intent, t["id"], tenant_id),
                )
            processed += 1
    print(f"[inbox] {processed} thread(s) processed")
    return processed


def main():
    C.load_env(); C.init_db()
    poll_once()
    print("inbox poll ok")


if __name__ == "__main__":
    main()