# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-10-30

### Added

**SLDR Autonomous Software Factory**
- Eight specialized agents (Product Analyst, Architect, Lead Developer, Frontend,
  Backend, DevOps, QA, Release Manager) with JSON input/output contracts.
- Artifact-based handoffs in `.opencode/handoffs/`, artifacts in `.opencode/artifacts/`.
- Pipeline state persistence in `.opencode/sldr_state.json` with resume support.
- Verification gates (build, test, lint, security) between every handoff.
- `/auto` command: `init`, `<requirements>`, `status`, `resume`, `gate <role>`.
- Global installation for OpenCode and OpenFable plus per-project installation.

**Dropshipping Operations Platform**
- Multi-tenant isolation with `tenant_id` scoping and per-tenant quotas.
- Stripe billing: three tiers, checkout, idempotent webhooks, invoices, proration,
  dunning, GMV ledger.
- Auth hardening: JWT access/refresh tokens, OAuth2, TOTP MFA, lockout,
  impersonation audit trail.
- Observability: structured JSON logging, circuit breakers, retry/backoff, SQLite WAL.
- Product research, margin floor protection, auto-repricing, supplier failover.
- Sample ordering with latency scoring and supplier demotion.
- Inbox AI with confidence gating and one-tap approval.
- Order tracking: plus-address aliases, IMAP poller, carrier detection.
- Playwright automation with profile lock, rate limiting, selector self-healing.
- Cross-listing to eBay / OfferUp / Nextdoor (dry-run mode).
- Background daemon with auto-start and auto-restart.
- First-run setup wizard (CLI and web UI).
- Production readiness audit (`python -m fbm.audit`).
- Docker and Docker Compose deployment (local and VPS) with Prometheus + Grafana.
- Standalone Windows `.exe` build (PyInstaller) and systemd unit file.

### Fixed
- `fbm/inbox.py`: corrected module imports (`fbm_core` → `fbm.core`,
  `returns` → `fbm.returns`) and `inbox_ai.draft()` signature.
- `fbm/billing.py`: aligned public API with the test contract.
- `fbm/web_pages.py`: added missing `jsonify` import for `/setup` endpoints.

## [0.2.0] — earlier
- Full implementation of all deliverables.
