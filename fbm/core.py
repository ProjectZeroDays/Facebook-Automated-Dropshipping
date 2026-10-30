"""
fbm/core.py — hardened runtime for the FB Marketplace toolset.

Kills six failure modes:
  1. concurrent runs on one profile  -> profile_lock()
  2. getting rate-limited            -> RateLimiter + looks_blocked()
  3. brittle DOM selectors           -> find() self-heal + calibrate
  4. silent breakage                 -> health() alerts
  5. leaked secrets                  -> load_env() with chmod 600
  6. scattered boilerplate           -> session() context manager

Env: FBM_PROFILE, FBM_DB, FBM_ENV, FBM_SELECTORS, FBM_STATE, ALERT_WEBHOOK
"""
from __future__ import annotations
import json, os, random, sys, time
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
PROFILE_DIR = os.getenv("FBM_PROFILE", "fb_profile")
SEL_PATH = Path(os.getenv("FBM_SELECTORS", "selectors.json"))
STATE_PATH = Path(os.getenv("FBM_STATE", "fbm_state.json"))


# ============================================================ 1. secrets
def load_env(path=None, enforce_perms=True):
    """Load .env into os.environ and force 600 perms on POSIX."""
    p = Path(path or os.getenv("FBM_ENV", ".env"))
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        if enforce_perms and os.name == "posix":
            mode = oct(p.stat().st_mode & 0o777)
            if mode != "0o600":
                try:
                    os.chmod(p, 0o600); print(f"[env] tightened {p} to 600")
                except Exception:
                    print(f"[env] WARNING {p} is {mode} -> run: chmod 600 {p}")
    return p


def require(var):
    v = os.getenv(var)
    if not v:
        raise SystemExit(f"[env] missing required var: {var}")
    return v


# ============================================================ 2. locking
LOCK_NAME = ".fbm.lock"


class ProfileLock:
    """Cross-platform exclusive lock so two scripts never share the profile."""
    def __init__(self, profile_dir=None, timeout=900):
        self.path = Path(profile_dir or PROFILE_DIR) / LOCK_NAME
        self.timeout = timeout
        self.fh = None

    def acquire(self, wait=True):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout
        while True:
            self.fh = open(self.path, "a+")
            try:
                if os.name == "posix":
                    import fcntl
                    fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    import msvcrt
                    msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
                self._stamp()
                return True
            except OSError:
                self.fh.close(); self.fh = None
                if not wait or time.time() > deadline:
                    return False
                time.sleep(random.uniform(1.5, 4.0))

    def _stamp(self):
        try:
            self.fh.seek(0); self.fh.truncate()
            self.fh.write(json.dumps({
                "pid": os.getpid(), "script": Path(sys.argv[0]).name,
                "since": datetime.now(timezone.utc).isoformat()}))
            self.fh.flush()
        except Exception:
            pass

    def holder(self):
        try:
            return json.loads(self.path.read_text()) or {}
        except Exception:
            return {}

    def release(self):
        try:
            if self.fh:
                if os.name == "posix":
                    import fcntl; fcntl.flock(self.fh, fcntl.LOCK_UN)
                else:
                    import msvcrt; msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
                self.fh.close()
        finally:
            self.fh = None


@contextmanager
def profile_lock(wait=True, timeout=900):
    lock = ProfileLock(timeout=timeout)
    if not lock.acquire(wait=wait):
        h = lock.holder()
        raise SystemExit(f"[lock] profile busy (held by pid {h.get('pid')} "
                         f"{h.get('script')} since {h.get('since')})")
    try:
        yield lock
    finally:
        lock.release()


# ============================================================ 3. rate limit
class RateLimiter:
    """Persisted token bucket with jitter + adaptive backoff."""
    def __init__(self, per_hour=60, per_day=400, min_gap=1.0, max_gap=4.0):
        self.per_hour, self.per_day = per_hour, per_day
        self.min_gap, self.max_gap = min_gap, max_gap
        self.multiplier = 1.0
        self.st = self._load()

    def _load(self):
        try: return json.loads(STATE_PATH.read_text())
        except Exception: return {"hours": {}, "days": {}, "last": 0}

    def _save(self):
        try: STATE_PATH.write_text(json.dumps(self.st))
        except Exception: pass

    def _count(self, bucket, key):
        return self.st.get(bucket, {}).get(key, 0)

    def _bump(self, bucket, key):
        self.st.setdefault(bucket, {})[key] = self._count(bucket, key) + 1

    def wait(self):
        now = time.time()
        gap = random.uniform(self.min_gap, self.max_gap) * self.multiplier
        since = now - self.st.get("last", 0)
        if since < gap:
            time.sleep(gap - since)
        h, d = datetime.now().strftime("%Y%m%d%H"), datetime.now().strftime("%Y%m%d")
        while self._count("hours", h) >= self.per_hour or self._count("days", d) >= self.per_day:
            print("[rate] hourly/daily cap hit, sleeping 30s"); time.sleep(30 * self.multiplier)
        self._bump("hours", h); self._bump("days", d)
        self.st["last"] = time.time(); self._save()

    def backoff(self, factor=1.6, cap=8.0):
        self.multiplier = min(cap, self.multiplier * factor)
        print(f"[rate] backoff -> x{self.multiplier:.1f}")

    def relax(self):
        self.multiplier = max(1.0, self.multiplier * 0.9)


# ============================================================ 4. block detect
BLOCK_HINTS = ("You're temporarily blocked", "Please try again later",
               "temporarily blocked", "This content isn't available")


def looks_blocked(page):
    try:
        body = page.inner_text("body")[:5000]
    except Exception:
        return False
    hit = any(h in body for h in BLOCK_HINTS)
    if hit:
        notify("block/challenge detected", "warn")
    return hit


# ============================================================ 5. selectors
DEFAULT_SELECTORS = {
    "login_email":  ["input[name='email']"],
    "title":        ["label:has-text('Title') input", "input[aria-label='Title']"],
    "price":        ["label:has-text('Price') input", "input[aria-label='Price']"],
    "description":  ["label:has-text('Description') textarea", "textarea[aria-label='Description']"],
    "category":     ["label:has-text('Category')"],
    "condition":    ["label:has-text('Condition')"],
    "next":         ["div[aria-label='Next']", "button:has-text('Next')", "span:has-text('Next')"],
    "publish":      ["div[aria-label='Publish']", "button:has-text('Publish')"],
    "renew":        ["text=Renew"],
    "more_options": ["[aria-label='More options']"],
    "file_input":   ["input[type='file']"],
    "orders_tab":   ["text=Orders", "a:has-text('Orders')"],
    "add_tracking": ["text=Add tracking", "button:has-text('Add tracking')"],
    "carrier_select": ["select[name='carrier']", "[aria-label='Carrier']"],
    "tracking_input": ["input[name='tracking']", "[aria-label='Tracking number']"],
    "confirm":      ["button:has-text('Confirm')", "button:has-text('Save')"],
    "sell_something": ["text=Sell something", "div:has-text('Sell something')"],
    "allow_offers": ["input[name='allow_offers']", "label:has-text('Allow offers')"],
}


def _learned():
    try: return json.loads(SEL_PATH.read_text())
    except Exception: return {}


def save_selector(key, sel):
    data = _learned(); data[key] = sel
    try: SEL_PATH.write_text(json.dumps(data, indent=2))
    except Exception: pass


def find(page, key, timeout=8000):
    """Try learned selector first, then defaults. Auto-heals on success."""
    learned = _learned().get(key)
    order = ([learned] if learned else []) + DEFAULT_SELECTORS.get(key, [])
    for sel in order:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            if learned != sel:
                save_selector(key, sel)
                print(f"[sel] healed '{key}' -> {sel}")
            return loc
        except Exception:
            continue
    raise TimeoutError(f"[sel] '{key}' not found; run login_once.py --calibrate")


def calibrate(page, keys=None):
    """Probe each selector on the current page and persist what works."""
    results = {}
    for key in (keys or DEFAULT_SELECTORS.keys()):
        ok = False
        for sel in DEFAULT_SELECTORS[key]:
            try:
                page.locator(sel).first.wait_for(state="visible", timeout=2500)
                save_selector(key, sel); ok = True; break
            except Exception:
                continue
        results[key] = ok
    return results


# ============================================================ 6. alerts + health
def notify(msg, level="info"):
    import requests
    hook = os.getenv("ALERT_WEBHOOK")
    if hook:
        try: requests.post(hook, json={"text": f"[fbm/{level}] {msg}"}, timeout=10)
        except Exception: pass


def health(label, count, min_expected=1):
    ok = count >= min_expected
    if not ok:
        notify(f"HEALTH: '{label}' returned {count} (< {min_expected})", "warn")
        print(f"[health] WARN '{label}' = {count}")
    return ok


# ============================================================ 7. session
def ensure_logged_in(page):
    page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    time.sleep(random.uniform(1.5, 2.5))
    if page.locator(DEFAULT_SELECTORS["login_email"][0]).count() > 0:
        print(">>> log in in the window, then press Enter")
        input()


def dismiss_modals(page):
    for label in ("Close", "Not now", "Allow all", "Only allow essential"):
        try:
            page.get_by_text(label, exact=False).first.click(timeout=1200)
            time.sleep(random.uniform(0.4, 0.9))
        except Exception:
            pass


@contextmanager
def session(headless=False, rate=None, lock=True, login=True):
    """Locked, rate-limited, logged-in browser session. Yields (page, limiter)."""
    from playwright.sync_api import sync_playwright
    load_env()
    lim = rate or RateLimiter()
    with (profile_lock() if lock else nullcontext()):
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                PROFILE_DIR, headless=headless,
                viewport={"width": 1366, "height": 900},
                user_agent=USER_AGENT,
                args=["--disable-blink-features=AutomationControlled"])
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            try:
                if login: ensure_logged_in(page)
                yield page, lim
            finally:
                ctx.close()


# ============================================================ 8. database
import sqlite3 as _sqlite3


DEFAULT_TENANT_ID = "default"

# Tables that hold per-tenant business data. Every read/write on these must be
# scoped by tenant_id so no cross-tenant data access is possible.
TENANT_ID_COLUMNS = {
    "skus": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "orders": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "samples": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "events": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "threads": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "listings": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "comps": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "pnl": "tenant_id TEXT NOT NULL DEFAULT 'default'",
    "drafts": "tenant_id TEXT NOT NULL DEFAULT 'default'",
}


def db_path():
    return os.getenv("FBM_DB", "fbm.sqlite")


def db():
    conn = _sqlite3.connect(db_path())
    conn.row_factory = _sqlite3.Row
    try:
        from fbm.observability import apply_wal
        apply_wal(conn)
    except Exception:
        pass
    return conn


def _ensure_tenant_id_columns(c):
    """Idempotently add tenant_id to tables created before multi-tenancy."""
    for table, coldef in TENANT_ID_COLUMNS.items():
        cols = [row["name"] for row in c.execute(f"PRAGMA table_info({table})").fetchall()]
        if "tenant_id" not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {coldef}")


def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS tenants(
            id TEXT PRIMARY KEY, name TEXT, email TEXT UNIQUE, plan TEXT DEFAULT 'starter',
            state TEXT DEFAULT 'TN', city TEXT, mode TEXT DEFAULT 'ship', status TEXT DEFAULT 'trialing',
            trial_ends TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, profile_dir TEXT,
            city TEXT, active INTEGER DEFAULT 1, listing_cap INTEGER DEFAULT 10,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS skus(
            sku TEXT PRIMARY KEY, title TEXT, price REAL, cost REAL, category TEXT,
            source TEXT, backup_source TEXT, active INTEGER DEFAULT 1, photos TEXT,
            tenant_id TEXT NOT NULL DEFAULT 'default');
        CREATE TABLE IF NOT EXISTS listings(
            id TEXT PRIMARY KEY, account TEXT, sku TEXT, query TEXT, title TEXT, price REAL,
            location TEXT, url TEXT, variant INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
            renewed INTEGER DEFAULT 0, posted_at TEXT, seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
            tenant_id TEXT NOT NULL DEFAULT 'default');
        CREATE TABLE IF NOT EXISTS comps(
            id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, title TEXT, price REAL,
            location TEXT, url TEXT, account TEXT, seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
            tenant_id TEXT NOT NULL DEFAULT 'default');
        CREATE TABLE IF NOT EXISTS orders(
            fingerprint TEXT PRIMARY KEY, account TEXT, sku TEXT, title TEXT, price REAL,
            buyer TEXT, address TEXT, status TEXT DEFAULT 'NEW', tracking TEXT, supplier TEXT,
            payload TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT,
            tenant_id TEXT NOT NULL DEFAULT 'default');
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, ref TEXT, detail TEXT,
            account TEXT, tenant_id TEXT NOT NULL DEFAULT 'default',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS pnl(
            id INTEGER PRIMARY KEY AUTOINCREMENT, month TEXT, revenue REAL, fees REAL,
            cogs REAL, refunds REAL, net REAL, orders INTEGER,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS samples(
            sku TEXT PRIMARY KEY, supplier TEXT, ordered_at TEXT, cost REAL,
            latency_days REAL, verdict TEXT,
            tenant_id TEXT NOT NULL DEFAULT 'default');
        CREATE TABLE IF NOT EXISTS drafts(
            id TEXT PRIMARY KEY, thread_id TEXT, text TEXT, confidence REAL,
            status TEXT, tenant_id TEXT NOT NULL DEFAULT 'default',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS threads(
            id TEXT PRIMARY KEY, title TEXT, last_msg TEXT, intent TEXT,
            replied_at TEXT, seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
            tenant_id TEXT NOT NULL DEFAULT 'default');
        CREATE TABLE IF NOT EXISTS webhook_events(
            event_id TEXT PRIMARY KEY, event_type TEXT, processed_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS processed_events(
            event_id TEXT PRIMARY KEY, kind TEXT, processed_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS invoices(
            invoice_id TEXT PRIMARY KEY, tenant_id TEXT, amount REAL,
            status TEXT DEFAULT 'open', stripe_invoice_id TEXT, due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS payment_failures(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT, failure_count INTEGER DEFAULT 0,
            last_failure TEXT, next_retry TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        _ensure_tenant_id_columns(c)
    try:
        from fbm.observability import ensure_db_healthy
        ensure_db_healthy()
    except Exception:
        pass


def tenant_scope(tenant_id: str = None) -> str:
    """Return the tenant_id to use, defaulting to DEFAULT_TENANT_ID."""
    return tenant_id or DEFAULT_TENANT_ID


def q_tenant(c, table: str, tenant_id: str, extra_where: str = "", extra_params: tuple = ()):
    """Build a tenant-scoped SELECT for *table*."""
    where = f"tenant_id=?" 
    params = [tenant_id]
    if extra_where:
        where += f" AND {extra_where}"
        params.extend(extra_params)
    return f"SELECT * FROM {table} WHERE {where}", tuple(params)