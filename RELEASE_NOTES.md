# Release v1.0.0 — Facebook Automated Dropshipping

**Release date:** 2026-10-30
**Author:** Trey A. Smith — Authenticated, Inc.

## Overview

First production release of the **Facebook Marketplace Dropshipping Ops** platform together with the
**SLDR (Software Development Life Cycle Roles) Autonomous Software Factory**.

This release delivers an autonomous, multi-tenant dropshipping operations engine plus an eight-agent
software factory that builds full-stack applications from raw requirements to production deployment
using artifact-based handoffs and verification gates.

## Highlights

### SLDR Autonomous Software Factory

- 8 specialized agents with explicit input/output contracts
  - Product Analyst → System Architect → Lead Developer
  - Frontend ‖ Backend ‖ DevOps (parallel)
  - QA Engineer → Release Manager
- Artifact-based handoffs (JSON) in `.opencode/handoffs/` — no chat-based context passing
- State persisted in `.opencode/sldr_state.json` for intelligent resume
- Verification gates between every handoff (build, test, lint, security)
- `/auto` command: `init`, `<requirements>`, `status`, `resume`, `gate <role>`
- Installed globally (OpenCode + OpenFable) and per-project

### Dropshipping Operations Platform

- Multi-tenant isolation with `tenant_id` row scoping and per-tenant quotas
- Stripe billing: 3 tiers (Starter $49 / Pro $99 / Agency $199), checkout, webhooks,
  idempotent event processing, invoices, proration, dunning, GMV ledger
- Auth hardening: JWT access/refresh, OAuth2, TOTP MFA, lockout, impersonation audit
- Observability: structured JSON logging, circuit breakers, retry/backoff, SQLite WAL
- Product research, margin floor protection, auto-repricing, supplier failover
- Sample ordering with latency scoring and supplier demotion
- Inbox AI with confidence gating and one-tap approval
- Order tracking via plus-address aliases + IMAP poller + carrier detection
- Playwright bot automation with profile lock, rate limiting, selector self-healing
- Cross-listing to eBay / OfferUp / Nextdoor (dry-run mode)
- Background daemon with auto-start and auto-restart
- First-run setup wizard (CLI and web UI)
- Production readiness audit (`python -m fbm.audit`)
- Docker / Docker Compose deployment (local and VPS) with Prometheus + Grafana
- Standalone Windows `.exe` build (PyInstaller) and systemd unit file

## Installation

```powershell
git clone https://github.com/ProjectZeroDays/Facebook-Automated-Dropshipping.git
cd Facebook-Automated-Dropshipping
.\deploy_local.ps1          # Windows
# or
./deploy_local.sh           # Linux / macOS
```

## Quick Start

```powershell
python .opencode/skills/sldr-autonomous-factory/auto_command.py init
python .opencode/skills/sldr-autonomous-factory/auto_command.py "A SaaS dashboard with Stripe billing and auth"
python .opencode/skills/sldr-autonomous-factory/auto_command.py status
```

## Verification

- 60 tests collected; core suites passing (billing, auth, inbox AI, econ, credits, lock, rate, regions)
- 25/25 Flask GET routes return HTTP 200
- 38 `fbm` modules import cleanly
- `python -m fbm.audit` → 0 critical issues (4 non-blocking config warnings)

## Known Limitations

- No official Facebook Marketplace API — browser automation only
- No native mobile app (PWA/Electron planned)
- Cross-listing runs in dry-run mode by default
- Polling-based updates (no WebSockets yet)
- Single-instance deployment (no horizontal scaling)
- Automated browsing may violate Facebook's Terms of Service — use at your own risk

## Breaking Changes

None — first release.

## Upgrade Notes

First release; follow `README.md` installation instructions.

## License

MIT — see [LICENSE](LICENSE).
