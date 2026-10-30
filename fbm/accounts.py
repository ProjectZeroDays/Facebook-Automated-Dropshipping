"""
fbm/accounts.py — multi-account registry, load-balanced assignment, photo variation.
"""
from __future__ import annotations
from pathlib import Path
from fbm import core as C


def add(name, city, cap=10):
    with C.db() as c:
        c.execute("INSERT OR IGNORE INTO accounts(name,profile_dir,city,listing_cap) "
                  "VALUES(?,?,?,?)", (name, f"fb_profile_{name}", city, cap))


def active():
    with C.db() as c:
        return c.execute("SELECT * FROM accounts WHERE active=1").fetchall()


def count_active(account):
    with C.db() as c:
        return c.execute("SELECT COUNT(*) n FROM listings WHERE account=? AND status='active'",
                         (account,)).fetchone()["n"]


def next_account():
    """Least-loaded active account still under its listing cap."""
    accs = [a for a in active() if count_active(a["name"]) < a["listing_cap"]]
    if not accs:
        raise SystemExit("[accounts] every account is at cap — add another profile")
    return sorted(accs, key=lambda a: count_active(a["name"]))[0]


def vary_photos(photos, account_name, sku):
    """Give each account a visually near-identical but binary-different image set."""
    try:
        from PIL import Image, ImageEnhance
    except ImportError:
        return photos
    idx = abs(hash(account_name)) % 3
    dest = Path("imgs/variants"); dest.mkdir(parents=True, exist_ok=True)
    out = []
    for i, p in enumerate(photos):
        p = p.strip()
        src = Path(p)
        if not src.exists():
            out.append(p); continue
        im = Image.open(src).convert("RGB")
        im = im.rotate([-0.4, 0.4, 0.0][idx], resample=Image.BICUBIC, expand=False)
        im = ImageEnhance.Brightness(im).enhance(1.0 + (idx - 1) * 0.015)
        w, h = im.size
        im = im.crop((1, 1, w - 1, h - 1))
        fp = dest / f"{sku}_{account_name}_{i}.jpg"
        im.save(fp, quality=88)
        out.append(str(fp))
    return out[idx:] + out[:idx]   # rotate cover photo per account