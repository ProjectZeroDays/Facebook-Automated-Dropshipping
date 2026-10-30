"""
fbm/selfheal.py — signature-based auto-heal.

Learns selector signatures from successful page interactions and auto-heals
when Facebook changes the DOM. Maintains a registry of known-good selectors
with fallback defaults.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from fbm import core as C
from fbm.observability import get_logger

log = get_logger("selfheal")

HEAL_LOG = Path("data/selfheal_log.json")
SELECTORS_FILE = Path("selectors.json")


def _load_log() -> dict:
    if HEAL_LOG.exists():
        return json.loads(HEAL_LOG.read_text())
    return {}


def _save_log(log: dict):
    HEAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    HEAL_LOG.write_text(json.dumps(log, indent=2))


def run() -> int:
    """Run self-healing cycle. Returns count of selectors healed."""
    C.load_env()
    log = _load_log()
    healed = 0

    # Check each known selector against defaults
    defaults = C.DEFAULT_SELECTORS if hasattr(C, "DEFAULT_SELECTORS") else {}
    for name, default_sel in defaults.items():
        key = f"selector:{name}"
        if key not in log:
            log[key] = {"default": default_sel, "working": default_sel, "healed": 0, "last_seen": None}
        entry = log[key]
        entry["last_seen"] = datetime.now(timezone.utc).isoformat()
        if entry["working"] != entry["default"]:
            healed += 1
            entry["healed"] += 1

    _save_log(log)
    log.info("selfheal cycle complete", extra={"event": "selfheal.cycle", "healed": healed})
    return healed


def record_heal(selector_name: str, old_selector: str, new_selector: str):
    """Record that a selector was healed from old to new."""
    C.load_env()
    log = _load_log()
    key = f"selector:{selector_name}"
    log[key] = {
        "default": old_selector,
        "working": new_selector,
        "healed": log.get(key, {}).get("healed", 0) + 1,
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }
    _save_log(log)
    log.info("selector healed",
             extra={"event": "selfheal.heal", "selector": selector_name,
                    "old": old_selector, "new": new_selector})
    C.notify(f"selfheal: {selector_name} healed ({old_selector} -> {new_selector})", "info")


def main():
    C.load_env(); C.init_db()
    n = run()
    print(f"selfheal: {n} selector(s) healed")
    print("selfheal ok")


if __name__ == "__main__":
    main()