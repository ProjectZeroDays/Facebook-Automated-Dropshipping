"""
fbm/config.py — tenant config: region, mode, fees. Replaces hardcoded Memphis/TN.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from urllib.parse import quote
from fbm import regions


PATH = Path(os.getenv("FBM_CONFIG", "config.json"))
DEFAULTS = {"state": "TN", "city": "Memphis", "mode": "ship",
            "currency": "USD", "radius_mi": 40, "auto_reprice": True}


def load():
    try: return {**DEFAULTS, **json.loads(PATH.read_text())}
    except Exception: return dict(DEFAULTS)


def save(**kw):
    cfg = {**load(), **kw}
    PATH.write_text(json.dumps(cfg, indent=2))
    return cfg


def fee_rate(mode=None):
    return {"ship": 0.10, "local": 0.0, "hybrid": 0.10}.get(mode or load()["mode"], 0.10)


def tax():
    return regions.profile(load()["state"])


def search_url(query):
    return f"https://www.facebook.com/marketplace/{load()['city'].lower()}/search?query={quote(query)}"


def listing_defaults():
    m = load()["mode"]
    return {"delivery": {"ship": "shipping only", "local": "local pickup", "hybrid": "both"}[m],
            "fee": fee_rate(m), "allow_negotiation": m != "ship"}


def validate():
    c, errs = load(), []
    if c["state"].upper() not in regions.STATES: errs.append(f"unknown state: {c['state']}")
    if not c.get("city"): errs.append("city required")
    if c["mode"] not in ("ship", "local", "hybrid"): errs.append(f"bad mode: {c['mode']}")
    return errs


def cli():
    import argparse, sys
    ap = argparse.ArgumentParser(prog="fbm-config")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("set"); s.add_argument("--state"); s.add_argument("--city"); s.add_argument("--mode")
    sub.add_parser("show"); sub.add_parser("check")
    a = ap.parse_args()
    if a.cmd == "set":
        save(**{k: v for k, v in {"state": a.state, "city": a.city, "mode": a.mode}.items() if v})
        print(load())
    elif a.cmd == "check":
        e = validate(); print("OK" if not e else "\n".join(e)); sys.exit(1 if e else 0)
    else:
        print(json.dumps(load(), indent=2))


if __name__ == "__main__":
    cli()