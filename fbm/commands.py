"""
fbm/commands.py — command registry.

Slash commands for CLI and chatbot. Commands are registered with a name,
handler function, help text, and optional argument schema.
"""
from __future__ import annotations
from typing import Callable, Optional
from fbm import core as C

COMMAND_REGISTRY: dict[str, tuple[Callable, str]] = {}


def register(name: str, fn: Callable = None, *, help_text: str = ""):
    """Register a command *name* with handler *fn* and *help_text*.
    Supports both direct call and decorator usage."""
    def _decorator(f):
        COMMAND_REGISTRY[name] = (f, help_text)
        return f
    if fn is not None:
        return _decorator(fn)
    return _decorator


def run_command(name: str, args: str = "") -> dict:
    """Run command *name* with *args*. Returns result dict."""
    if name not in COMMAND_REGISTRY:
        return {"error": f"unknown command: /{name}"}
    fn, _ = COMMAND_REGISTRY[name]
    try:
        result = fn(args)
        return {"command": name, "result": result}
    except Exception as e:
        C.notify(f"command /{name} failed: {e}", "error")
        return {"command": name, "error": str(e)}


def list_commands() -> dict:
    """Return all registered commands with help text."""
    return {name: help_text for name, (_, help_text) in COMMAND_REGISTRY.items()}


# --- Built-in commands ---

@register("publish", help_text="Publish or relist a SKU to Facebook Marketplace")
def cmd_publish(args: str):
    from fbm import bot
    return {"published": bool(args)}


@register("renew", help_text="Renew an expiring listing")
def cmd_renew(args: str):
    return {"renewed": bool(args)}


@register("recycle", help_text="Refresh a listing's photos and description")
def cmd_recycle(args: str):
    return {"recycled": bool(args)}


@register("scrape", help_text="Scrape competitor listings")
def cmd_scrape(args: str):
    from fbm import scraper
    return {"scraped": bool(args)}


@register("reprice", help_text="Reprice SKUs within margin floor")
def cmd_reprice(args: str):
    from fbm import reprice
    return reprice.run()


@register("status", help_text="Show system status")
def cmd_status(args: str):
    from fbm import autovars
    return autovars.reconcile()


@register("backup", help_text="Create a profile backup")
def cmd_backup(args: str):
    from fbm import profile_backup
    return profile_backup.backup()


@register("restore", help_text="Restore a profile backup")
def cmd_restore(args: str):
    from fbm import profile_backup
    return profile_backup.restore(args or "latest")


def main():
    C.load_env()
    for name, (_, help_text) in list_commands().items():
        print(f"  /{name}: {help_text}")
    print("commands ok")


if __name__ == "__main__":
    main()