"""
fbm/inbox_ai.py — LLM-drafted replies with confidence gating + one-tap approve.

  python -m fbm.inbox_ai --once            # draft/send for unmatched threads
  python -m fbm.inbox_ai --once --dry
"""
from __future__ import annotations
import argparse, json, os, re
from pathlib import Path
import requests
from fbm import core as C
from fbm import returns as Returns

AUTO_THRESHOLD = float(os.getenv("INBOX_AUTO_THRESHOLD", "0.85"))
POLICY = Path("policy.md")


def context(raw, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        o = c.execute("SELECT * FROM orders WHERE tenant_id=? ORDER BY created_at DESC LIMIT 3",
                      (tenant_id,)).fetchall()
    return ("POLICY:\n" + (POLICY.read_text() if POLICY.exists() else "") +
            "\nRECENT ORDERS:\n" +
            "\n".join(f"- {x['title']} status={x['status']} trk={x['tracking'] or '-'}" for x in o))


def draft(raw, tenant_id=C.DEFAULT_TENANT_ID):
    key = os.getenv("OPENAI_API_KEY")
    if not key: return None
    prompt = (f"{context(raw, tenant_id)}\n\nBUYER MESSAGE:\n{raw}\n\n"
              "Write a short, warm Marketplace reply that follows policy exactly. "
              'Return strict JSON {"reply":"","confidence":0.0,"needs_human":false}. '
              "confidence<0.85 or refunds over $60 => needs_human true.")
    r = requests.post(f"{os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1')}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": os.getenv("INBOX_MODEL","gpt-4o-mini"), "temperature": 0.3,
              "messages": [{"role": "user", "content": prompt}]}, timeout=45)
    r.raise_for_status()
    m = re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S)
    return json.loads(m.group(0)) if m else None


def few_shot(tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        rows = c.execute("SELECT thread_id,text FROM drafts WHERE status='approved' AND tenant_id=? "
                         "ORDER BY created_at DESC LIMIT 5", (tenant_id,)).fetchall()
    return "\n".join(f"- {r['text']}" for r in rows)


def process(thread_id, raw, dry=False, tenant_id=C.DEFAULT_TENANT_ID):
    d = draft(raw)
    if not d: return False
    auto = d.get("confidence", 0) >= AUTO_THRESHOLD and not d.get("needs_human")
    with C.db() as c:
        c.execute("INSERT OR REPLACE INTO drafts(id,thread_id,text,confidence,status,tenant_id,created_at) "
                  "VALUES(?,?,?,?,?,?,datetime('now'))",
                  (thread_id, thread_id, d["reply"], d.get("confidence", 0),
                   "auto_sent" if auto and not dry else "pending", tenant_id))
    if auto and not dry:
        C.notify(f"AI auto-replied ({d.get('confidence'):.2f}): {d['reply'][:60]}...")
    else:
        C.notify(f"draft needs approval: {d['reply'][:80]}...")
    return True


def approve(thread_id, text=None, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        row = c.execute("SELECT text FROM drafts WHERE thread_id=? AND tenant_id=?",
                        (thread_id, tenant_id)).fetchone()
        c.execute("UPDATE drafts SET status='approved', text=COALESCE(?,text) WHERE thread_id=? AND tenant_id=?",
                  (text, thread_id, tenant_id))
    return row["text"] if row else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    C.load_env(); C.init_db()
    with C.db() as c:
        threads = c.execute("SELECT id,last_msg FROM threads WHERE replied_at IS NULL "
                            "AND intent IS NULL AND tenant_id=?",
                            (C.DEFAULT_TENANT_ID,)).fetchall()
    for t in threads:
        process(t["id"], t["last_msg"] or "", dry=a.dry)