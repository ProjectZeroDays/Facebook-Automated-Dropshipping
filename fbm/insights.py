"""
fbm/insights.py — views/saves scraper.

Scrapes views, saves, and engagement metrics from Facebook Marketplace
listings to inform pricing and ranking decisions.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
from fbm import core as C

INSIGHTS_TABLE = """
CREATE TABLE IF NOT EXISTS listing_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    date TEXT NOT NULL,
    UNIQUE(sku, date)
)
"""


def run(window: int = 7, tenant_id=C.DEFAULT_TENANT_ID) -> list:
    """Scrape insights for the last *window* days. Returns list of insight dicts."""
    C.load_env()
    C.init_db()

    # Ensure insights table exists
    with C.db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS listing_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            messages INTEGER DEFAULT 0,
            date TEXT NOT NULL,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            UNIQUE(sku, date, tenant_id)
        )""")

    insights = []
    end = datetime.now()
    for i in range(window):
        day = (end - timedelta(days=i)).strftime("%Y-%m-%d")
        with C.db() as c:
            rows = c.execute(
                "SELECT sku, views, saves, messages FROM listing_insights WHERE date=? AND tenant_id=?",
                (day, tenant_id),
            ).fetchall()
            for r in rows:
                insights.append(dict(r))

    return insights


def record(sku: str, views: int = 0, saves: int = 0, messages: int = 0,
           tenant_id=C.DEFAULT_TENANT_ID):
    """Record insight metrics for a SKU on the current day."""
    today = datetime.now().strftime("%Y-%m-%d")
    with C.db() as c:
        c.execute(
            "INSERT OR REPLACE INTO listing_insights(sku, views, saves, messages, date, tenant_id) "
            "VALUES(?,?,?,?,?,?)",
            (sku, views, saves, messages, today, tenant_id),
        )


def main():
    C.load_env(); C.init_db()
    ins = run()
    print(json.dumps(ins, indent=2, default=str) if (json := __import__("json")) else ins)
    print("insights ok")


if __name__ == "__main__":
    main()