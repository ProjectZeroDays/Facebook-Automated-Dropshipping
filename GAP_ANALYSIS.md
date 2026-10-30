================================================================================
GAP ANALYSIS — FB Dropshipper Production Readiness
================================================================================
Date: 2026-10-27
Project: FB Dropshipper (Autonomous Facebook Marketplace Dropshipping Ops)
Developer: Trey A. Smith, Authenticated, Inc.
Status: PRE-PRODUCTION — NOT READY FOR COMMERCIAL DEPLOYMENT

================================================================================
1. EXECUTIVE SUMMARY
================================================================================

The FB Dropshipper project is a comprehensive autonomous Facebook Marketplace
dropshipping operations platform with a full agentic ecosystem (commands,
agents, workflows, MCP, plugins, security). The core engine is implemented
and functional (31/31 tests pass, all modules import cleanly, app is live
on http://127.0.0.1:5000).

However, the project is NOT production-ready for commercial deployment.
Critical gaps exist in: multi-tenant isolation, Stripe billing integration,
production authentication, mobile/desktop deployment, observability, error
handling, rate-limit safety, and legal/compliance infrastructure.

================================================================================
2. GAP ANALYSIS BY CATEGORY
================================================================================

---------------------------------------------------------------
2.1 AUTHENTICATION & AUTHORIZATION — CRITICAL GAP
---------------------------------------------------------------

CURRENT STATE:
  - auth.py: passkeys, passwords, TOTP, resets, step-up, audit — 49 lines
  - authroutes.py: all auth endpoints — 71 lines
  - rp.py: RP_ID/ORIGIN resolution — 42 lines
  - totp.py: secret, QR, recovery codes — 34 lines
  - signup.py: signup → Stripe → finish — 49 lines
  - sessions: Flask session-based, no JWT/refresh tokens

GAPS:
  [ ] No OAuth2/OpenID Connect provider integration (Google, Facebook, Apple)
  [ ] No JWT access/refresh token rotation
  [ ] No session invalidation on logout across devices
  [ ] No multi-factor authentication enforcement policies
  [ ] No admin impersonation audit trail with re-authentication
  [ ] No password breach monitoring (HaveIBeenPwned integration)
  [ ] No account lockout after failed attempts (rate limiting exists but basic)

SEVERITY: CRITICAL — blocks all commercial use

---------------------------------------------------------------
2.2 MULTI-TENANCY & DATA ISOLATION — CRITICAL GAP
---------------------------------------------------------------

CURRENT STATE:
  - tenants.py: tenant list, impersonate, comp, gate, rotate, export — 15 lines
  - vault.py: per-tenant Fernet secrets — 28 lines
  - flags.py: global + per-tenant feature flags — 49 lines
  - credits.py: ledger, referral, guards, clawback — 81 lines
  - integrations.py: registry + connect flow — 85 lines

GAPS:
  [ ] No row-level security on SQLite tables — all queries filter by tenant_id
      manually, easy to miss and leak data between tenants
  [ ] No tenant provisioning workflow (signup creates tenant, but no approval
      flow, no tier-based provisioning limits)
  [ ] No tenant data export/deletion (GDPR/CCPA right to erasure)
  [ ] No tier-based feature enforcement (starter/pro/agency flags exist but
      not enforced at query/API level)
  [ ] No tenant usage quotas (listings, publishes, AI messages tracked but
      not enforced)
  [ ] No shared-nothing architecture — single SQLite DB for all tenants

SEVERITY: CRITICAL — data leakage risk between customers

---------------------------------------------------------------
2.3 BILLING & PAYMENTS — CRITICAL GAP
---------------------------------------------------------------

CURRENT STATE:
  - billing.py: plans, checkout, wallets, verify, activate — 30 lines
  - payments.py: Apple/Google/Venmo connect links — 35 lines (URLs only)
  - credits.py: dollar credits, referral, clawback — 81 lines
  - webhooks.py: Stripe webhook handler + idempotency store — 187 lines
  - tax.py: monthly P&L + 1099-K tracker — 44 lines

GAPS:
  [ ] Stripe integration not tested end-to-end (no STRIPE_SECRET_KEY in .env)
  [ ] No invoice generation/PDF delivery
  [ ] No proration logic for plan changes mid-cycle
  [ ] No dunning management (failed payment retry with escalating intervals)
  [ ] No tax calculation at point of sale (only post-hoc P&L reporting)
  [ ] No refund/chargeback handling workflow
  [ ] No metered billing for overages (AI messages, publishes beyond cap)
  [ ] No affiliate/referral payout tracking (credits exist but no cash payout)

SEVERITY: CRITICAL — cannot collect revenue without this

---------------------------------------------------------------
2.4 MOBILE & DESKTOP DEPLOYMENT — MAJOR GAP
---------------------------------------------------------------

CURRENT STATE:
  - Dockerfile: playwright base + Xvfb + cron — containerized
  - docker-compose.yml: worker + dashboard services
  - electron/: Electron `.exe` plan exists but not implemented
  - PWA plan: documented but not implemented
  - No mobile app (iOS/Android) for shop owners

GAPS:
  [ ] Electron desktop app not built (documented in pyproject.toml but no code)
  [ ] PWA not implemented (no service worker, no manifest, no offline mode)
  [ ] No iOS/Android mobile app for on-the-go shop management
  [ ] No code signing (EV certificate for Windows SmartScreen avoidance)
  [ ] No auto-updater for desktop clients
  [ ] Docker multi-arch builds not configured (amd64 only, no arm64)

SEVERITY: MAJOR — limits market reach to technical users only

---------------------------------------------------------------
2.5 OBSERVABILITY & MONITORING — MAJOR GAP
---------------------------------------------------------------

CURRENT STATE:
  - metrics.py: Prometheus exporter — 24 lines
  - deadman.py: healthchecks.io pings + two-strike escalation — 19 lines
  - ops/prometheus.yml: scrape config
  - ops/grafana/: dashboards + alerts provisioned
  - dashboard.py: /healthz, /metrics endpoints

GAPS:
  [ ] No structured logging with correlation IDs (logs are unstructured files)
  [ ] No distributed tracing for cross-service requests
  [ ] No real-time alerting (Slack/Discord/Telegram webhook exists but not
      integrated with Prometheus Alertmanager)
  [ ] No SLO/SLA tracking (uptime, latency, error budgets)
  [ ] No synthetic monitoring (probing key endpoints periodically)
  [ ] No log aggregation (ELK stack or similar)
  [ ] No incident response runbook automation

SEVERITY: MAJOR — cannot operate at scale without observability

---------------------------------------------------------------
2.6 ERROR HANDLING & RESILIENCE — MAJOR GAP
---------------------------------------------------------------

CURRENT STATE:
  - selfheal.py: signature-based auto-fix for selectors — 66 lines
  - session_guard.py: auto-relogin + TOTP — 80 lines
  - profile_backup.py: encrypted backup/restore — 45 lines
  - deadman.py: healthchecks + escalation — 19 lines
  - fbm_core.py: profile lock, rate limiter, block detection — 364 lines

GAPS:
  [ ] No circuit breakers for external API calls (Stripe, OpenAI, supplier APIs)
  [ ] No retry with exponential backoff on transient failures (partial)
  [ ] No graceful degradation when LLM backend is down
  [ ] No database connection pooling (SQLite, single connection)
  [ ] No WAL mode or SQLite corruption recovery
  [ ] No backup verification (backups created but not tested for restore)
  [ ] No disaster recovery plan (multi-region, point-in-time recovery)

SEVERITY: MAJOR — single point of failure, data loss risk

---------------------------------------------------------------
2.7 RATE LIMIT & ACCOUNT SAFETY — MAJOR GAP
---------------------------------------------------------------

CURRENT STATE:
  - fbm_core.py: RateLimiter token bucket (hourly/daily caps, jitter) — present
  - bot_rules.py: editable rules + hard limits — 78 lines
  - facebook compliance docs: policy restrictions documented

GAPS:
  [ ] No Facebook account health monitoring (cancellation rate, response time)
  [ ] No automated warm-up schedule for new accounts
  [ ] No violation detection (prohibited categories, counterfeit claims)
  [ ] No appeal workflow for account restrictions/suspensions
  [ ] No multi-account reputation isolation (one banned account affects others)
  [ ] No shipping deadline enforcement (3-business-day clock not tracked)

SEVERITY: MAJOR — account bans destroy customer businesses

---------------------------------------------------------------
2.8 TESTING & QUALITY ASSURANCE — MAJOR GAP
---------------------------------------------------------------

CURRENT STATE:
  - tests/: 20 test files, 31 tests pass
  - conftest.py: tmp DB/env fixture + path shim
  - fakes.py: FakePage/FakeLocator for Playwright testing
  - .pre-commit-config.yaml: ruff, hooks, module smoke, pytest-fast
  - pyproject.toml: packaging, ruff/pytest config

GAPS:
  [ ] No end-to-end tests (Playwright against real Facebook login)
  [ ] No load/performance testing
  [ ] No security penetration testing
  [ ] No chaos engineering (failure injection)
  [ ] No test coverage enforcement (cov-fail-under not configured)
  [ ] No mutation testing
  [ ] No API contract testing

SEVERITY: MAJOR — production regressions likely

---------------------------------------------------------------
2.9 LEGAL & COMPLIANCE — MAJOR GAP
---------------------------------------------------------------

CURRENT STATE:
  - LICENSE: Custom Authenticated, Inc. proprietary license (just added)
  - TERMS.md: subscription terms, fair use — placeholder
  - PRIVACY.md: data collection, retention, subprocessors — placeholder
  - SECURITY.md: threat model, key rotation, recovery ladder — placeholder
  - docs/compliance.md: TN LLC, business tax, 1099-K — documented
  - tax.py: 1099-K tracking, monthly P&L — 44 lines

GAPS:
  [ ] Terms of Service not finalized (placeholder only)
  [ ] Privacy Policy not finalized (placeholder only)
  [ ] No cookie consent banner
  [ ] No data processing agreement (DPA) for EU customers
  [ ] No trademark review ("Facebook" in name may violate Meta's IP policy)
  [ ] No FTC disclosure requirements for dropshipping
  [ ] No sales tax nexus tracking beyond TN
  [ ] No terms acceptance tracking per tenant

SEVERITY: MAJOR — legal exposure for customers and Authenticated, Inc.

================================================================================
3. SUMMARY OF BLOCKERS TO PRODUCTION
================================================================================

CRITICAL (must fix before any paying customer):
  1. Multi-tenant data isolation — row-level security, tenant quotas
  2. Stripe billing end-to-end — tested payments, invoices, dunning
  3. Authentication hardening — OAuth2, JWT, session management
  4. Legal — finalized ToS, Privacy Policy, trademark review

MAJOR (must fix before scaling beyond beta):
  5. Observability — structured logging, tracing, alerting integration
  6. Mobile/Desktop — Electron app, PWA, mobile app
  7. Error resilience — circuit breakers, retry logic, backup verification
  8. Rate limit & account safety — health monitoring, appeal workflow
  9. Testing — E2E, load, security, coverage enforcement
  10. Legal compliance — ToS, Privacy, cookie consent, DPA, tax nexus

MINOR (polish for public launch):
  11. Multi-arch Docker builds
  12. Auto-updater for desktop clients
  13. Code signing (EV certificate)
  14. Synthetic monitoring
  15. Incident response runbook automation

================================================================================
4. ESTIMATED EFFORT
================================================================================

  Critical gaps: 6-8 weeks (2 developers)
  Major gaps:    8-12 weeks (2 developers)
  Minor gaps:    2-4 weeks (1 developer)
  Total:         16-24 weeks to full production readiness

================================================================================
5. IMMEDIATE NEXT STEPS (30 DAYS)
================================================================================

  Week 1:  Implement row-level tenant security, finalize Stripe integration
  Week 2:  Add OAuth2 + JWT authentication, complete Terms/Privacy
  Week 3:  Build observability stack (logging, tracing, alerting)
  Week 4:  Beta launch with 5 design partners, collect feedback

================================================================================
END OF GAP ANALYSIS
================================================================================
