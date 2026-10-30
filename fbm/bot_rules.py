"""
fbm/bot_rules.py — bot behaviour with user-editable rules inside hard limits.
"""
from __future__ import annotations
import json, re
from datetime import datetime
from fbm import core as C


DEFAULTS = {
  "off_topic_action": "minimal",
  "minimal_replies": ["?", "What?", "Hmm?", "Sorry?"],
  "canned_off_topic": "Not sure on that one - ask me about the item and I'll help!",
  "max_replies_per_thread": 6,
  "quiet_hours": [22, 7],
  "language": "en",
  "auto_send_threshold": 0.85,
  "tone": "friendly-short",
  "blocked_keywords": ["crypto","loan","wholesale","rent","job"],
  "allowed_topics": ["product","price","shipping","returns","order","availability"],
}

HARD_LIMITS = {
  "auto_send_threshold": (0.50, 0.99),
  "max_replies_per_thread": (1, 12),
  "return_days": (0, 90),
}
NEVER_PROMISE_DATE = True
MUST_INCLUDE_POLICIES = True

TOPIC_PAT = {
  "order":     r"\b(order|tracking|track|shipped|arrive|delivered|where)\b",
  "returns":   r"\b(return|refund|money back|exchange)\b",
  "shipping":  r"\b(ship|deliver|how long|when|cost to ship)\b",
  "price":     r"\b(price|cost|cheaper|discount|offer|negotiat|\$)\b",
  "availability": r"\b(available|in stock|still have|left)\b",
  "product":   r"\b(color|size|material|dimension|fit|works with|compatible|quality)\b",
}


def rules(tenant_id):
    with C.db() as c:
        r = c.execute("SELECT json FROM bot_rules WHERE tenant_id=?", (tenant_id,)).fetchone()
    return {**DEFAULTS, **(json.loads(r["json"]) if r else {})}


def save_rules(tenant_id, patch):
    r = {**rules(tenant_id), **patch}
    for k, (lo, hi) in HARD_LIMITS.items():
        if k in r and isinstance(r[k], (int, float)):
            r[k] = max(lo, min(hi, r[k]))
    with C.db() as c:
        c.execute("INSERT INTO bot_rules(tenant_id,json) VALUES(?,?) "
                  "ON CONFLICT(tenant_id) DO UPDATE SET json=excluded.json",
                  (tenant_id, json.dumps(r)))
    return r


def classify(text, r):
    t = text.lower()
    if any(k in t for k in r["blocked_keywords"]): return "off_topic"
    for topic, pat in TOPIC_PAT.items():
        if re.search(pat, t): return topic
    return "off_topic"


def in_quiet_hours(r, now=None):
    now = now or datetime.now()
    h0, h1 = r["quiet_hours"]
    h = now.hour
    return (h >= h0 or h < h1) if h0 > h1 else (h0 <= h < h1)


def decide(tenant_id, text, thread_count=0):
    r = rules(tenant_id)
    topic = classify(text, r)
    if thread_count >= r["max_replies_per_thread"]:
        return {"action": "silent", "reason": "reply cap reached"}
    if in_quiet_hours(r):
        return {"action": "hold", "reason": "quiet hours"}
    if topic == "off_topic":
        act = r["off_topic_action"]
        if act == "silent":
            return {"action": "silent", "topic": topic}
        if act == "minimal":
            return {"action": "reply", "topic": topic,
                    "text": r["minimal_replies"][thread_count % len(r["minimal_replies"])]}
        return {"action": "reply", "topic": topic, "text": r["canned_off_topic"]}
    return {"action": "draft", "topic": topic}