"""
fbm/email_ingest.py — read supplier shipping emails, hand them to tracking.ingest().
"""
from __future__ import annotations
import email, imaplib, os, re
import tracking
from fbm import core as C


def _body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return re.sub("<[^>]+>", " ", part.get_payload(decode=True).decode(errors="ignore"))
    return msg.get_payload(decode=True).decode(errors="ignore")


def poll(limit=50):
    host, user, pw = os.getenv("IMAP_HOST"), os.getenv("IMAP_USER"), os.getenv("IMAP_PASS")
    if not all((host, user, pw)):
        return 0
    M = imaplib.IMAP4_SSL(host); M.login(user, pw); M.select("INBOX")
    _, data = M.search(None, "(UNSEEN)")
    n = 0
    for num in data[0].split()[-limit:]:
        _, msg = M.fetch(num, "(RFC822)")
        m = email.message_from_bytes(msg[0][1])
        if tracking.ingest({"to": m.get("To", ""), "subject": m.get("Subject", ""),
                            "body": _body(m), "from": m.get("From", "")}):
            n += 1
        M.store(num, "+FLAGS", "\\Seen")
    M.logout(); return n


if __name__ == "__main__":
    C.load_env(); print(f"ingested {poll()}")