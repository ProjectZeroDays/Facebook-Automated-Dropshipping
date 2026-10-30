# FBM Ops — Runbook

Operational manual for the Facebook Marketplace dropshipping stack.

## 1. Architecture at a glance

| Layer | Modules | Runs on |
|---|---|---|
| Runtime | fbm_core | every script |
| Content | copy_generator → fbm_validate | daily / on SKU change |
| Publishing | fb_marketplace_bot, groups, crosslist_post | cron |
| Intelligence | competitor_scraper → targets_builder → reprice | nightly |
| Orders | sale_watcher → n8n → suppliers → tracking → email_ingest | every 5 min |
| Comms | inbox_poller, inbox_ai, returns | every 10 min |
| Quality | samples, session_guard, profile_backup | scheduled |
| Ops | dashboard, metrics, deadman, tax | always |

## 2. First deploy (once)

```bash
git clone <repo> fbm && cd fbm
cp .env.example .env && chmod 600 .env
docker compose build
docker compose up -d
python -m fbm.login_once --calibrate --orders
python -m fbm.bootstrap
python -m fbm.copygen --in skus.csv --out inventory.csv
python -m fbm.validate --in inventory.csv --fix
```

## 3. Steady-state operations

**Daily:** Check dashboard, clear orders needing action, approve AI drafts.
**Weekly:** Backup, review insights, add 5-10 SKUs.
**Monthly:** tax.py --export, review sample verdicts, rotate API keys.