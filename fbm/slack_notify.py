import os, requests

def notify_slack(msg: str):
    url = os.getenv("ALERT_WEBHOOK", "")
    if url:
        try:
            requests.post(url, json={"text": msg}, timeout=5)
        except Exception:
            pass
