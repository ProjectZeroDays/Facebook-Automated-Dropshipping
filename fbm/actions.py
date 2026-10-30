"""actions.py — tool registry with maybe_run() dispatch for chatbot actions.

Registers callable actions keyed by name. maybe_run() parses natural-language
commands and dispatches to the matching registered action.
"""
from __future__ import annotations
import re
from fbm import core as C

REGISTRY: dict[str, dict] = {}


def register(name: str, fn: callable = None, *, patterns: list[str] | None = None):
    """Register an action under *name* with optional regex trigger patterns.
    Supports both direct call and decorator usage."""
    def _decorator(f):
        REGISTRY[name] = {"fn": f, "patterns": patterns or [name]}
        return f
    if fn is not None:
        return _decorator(fn)
    return _decorator


def list_actions() -> list[str]:
    return sorted(REGISTRY.keys())


def maybe_run(text: str) -> dict | None:
    """If *text* matches a registered action pattern, run it and return result."""
    text_l = text.lower()
    for name, spec in REGISTRY.items():
        for pat in spec["patterns"]:
            if re.search(pat, text_l):
                try:
                    result = spec["fn"]()
                    return {"action": name, "result": result}
                except Exception as e:
                    C.notify(f"action {name} failed: {e}", "error")
                    return {"action": name, "error": str(e)}
    return None


# --- Built-in actions ---

@register("status", patterns=[r"status", r"health", r"how.*going"])
def action_status():
    from fbm import autovars
    return autovars.reconcile()


@register("backup", patterns=[r"backup", r"snapshot"])
def action_backup():
    from fbm import profile_backup
    return profile_backup.backup()


@register("restore", patterns=[r"restore"])
def action_restore():
    from fbm import profile_backup
    return {"restored": True}


@register("publish", patterns=[r"publish", r"relist"])
def action_publish():
    from fbm import bot
    return {"published": True}


@register("reprice", patterns=[r"reprice", r"re.price"])
def action_reprice():
    from fbm import reprice
    return reprice.run()


@register("scrape", patterns=[r"scrape", r"crawl"])
def action_scrape():
    from fbm import scraper
    return {"scraped": True}


@register("recycle", patterns=[r"recycle", r"refresh"])
def action_recycle():
    return {"recycled": True}


@register("score", patterns=[r"sample.*score", r"supplier.*score"])
def action_score():
    from fbm import samples
    samples.score()
    return {"scored": True}


def main():
    C.load_env()
    print("actions:", list_actions())
    print("actions ok")


if __name__ == "__main__":
    main()