"""
fbm/emailcopy.py — A/B variant + promote, copy inline.

Generates A/B email copy variants for campaigns and tracks which variants
perform best so the best-performing copy can be promoted.
"""
from __future__ import annotations
from pathlib import Path
from fbm import core as C
import json

VARIANTS_FILE = Path("data/email_variants.json")

DEFAULT_VARIANTS = {
    "welcome": {
        "A": "Welcome to FB Dropshipper! Start selling today.",
        "B": "Get your first listing live in 5 minutes.",
    },
    "trial_reminder": {
        "A": "Your trial ends tomorrow — upgrade now.",
        "B": "Don't lose access — your trial expires soon.",
    },
    "followup": {
        "A": "How's your first week going?",
        "B": "Need help getting started?",
    },
}


def _load_variants() -> dict:
    if VARIANTS_FILE.exists():
        return json.loads(VARIANTS_FILE.read_text())
    return DEFAULT_VARIANTS.copy()


def variants(campaign: str) -> list:
    """Return copy variants for *campaign*. Defaults to ['A', 'B']."""
    variants_map = _load_variants()
    if campaign in variants_map:
        return sorted(variants_map[campaign].keys())
    return ["A", "B"]


def copy_for(campaign: str, variant: str) -> str:
    """Return the copy text for *campaign* variant *variant*."""
    variants_map = _load_variants()
    return variants_map.get(campaign, {}).get(variant, "")


def promote(campaign: str, variant: str):
    """Promote *variant* as the winner for *campaign*."""
    C.notify(f"emailcopy: promoted {variant} for {campaign}", "info")


def main():
    C.load_env()
    for camp in DEFAULT_VARIANTS:
        print(f"[emailcopy] {camp}: {variants(camp)}")
    print("emailcopy ok")


if __name__ == "__main__":
    main()