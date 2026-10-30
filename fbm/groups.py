"""
fbm/groups.py — auto-post listings into local buy/sell groups.

Posts each listing into up to N local groups for 5–10× reach. groups.txt = one
group ID or slug per line.
"""
from __future__ import annotations
from pathlib import Path
from fbm import core as C


def load_groups():
    p = Path("groups.txt")
    if not p.exists(): return []
    return [g.strip() for g in p.read_text().splitlines() if g.strip() and not g.startswith("#")]


def post_to_groups(page, lim, item, max_groups=10):
    from fbm import bot as Bot
    done = 0
    for g in load_groups()[:max_groups]:
        try:
            page.goto(f"https://www.facebook.com/groups/{g}/buy_sell_discussion",
                      wait_until="domcontentloaded")
            lim.wait(); C.dismiss_modals(page)
            try: C.find(page, "sell_something", timeout=4000).click()
            except Exception: pass
            Bot.publish_listing(page, item)
            done += 1
            print(f"posted to group {g}")
        except Exception as e:
            print(f"group {g} failed: {e}"); C.notify(f"group post failed {g}: {e}", "warn")
    return done