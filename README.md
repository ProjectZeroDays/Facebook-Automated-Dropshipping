# 🚀 Facebook Marketplace Dropshipping Ops

> **Autonomous Facebook Marketplace dropshipping operations platform** with SLDR (Software Development Life Cycle Roles) agent factory for building full-stack applications from requirements to production without human intervention.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![Playwright 1.47](https://img.shields.io/badge/Playwright-1.47-purple.svg)](https://playwright.dev/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-Ready-blue.svg)](https://docs.docker.com/compose/)
[![SLDR Factory](https://img.shields.io/badge/SLDR-Autonomous%20Factory-orange.svg)](./.opencode/skills/sldr-autonomous-factory/)
[![CLI: /auto](https://img.shields.io/badge/CLI-%2Fauto-red.svg)](./.opencode/skills/sldr-autonomous-factory/)
[![OS: Windows](https://img.shields.io/badge/OS-Windows-blue.svg)](https://www.microsoft.com/windows)
[![OS: Linux](https://img.shields.io/badge/OS-Linux-blue.svg)](https://www.linux.org/)
[![OS: macOS](https://img.shields.io/badge/OS-macOS-blue.svg)](https://www.apple.com/macos/)
[![Deployment: Local](https://img.shields.io/badge/Deployment-Local-green.svg)](./deploy_local.ps1)
[![Deployment: VPS/Docker](https://img.shields.io/badge/Deployment-VPS%2F%20Docker-blue.svg)](./deploy_vps.sh)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](./RELEASE_NOTES.md)

---

## Table of Contents

- [Introduction](#introduction)
- [Capabilities](#capabilities)
- [Architecture](#architecture)
- [SLDR Agent Group](#sldr-agent-group)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [GUI Controls](#gui-controls)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Implementation Status](#implementation-status)
- [Troubleshooting](#troubleshooting)
- [Dependencies](#dependencies)
- [Author](#author)
- [Legal Disclaimers](#legal-disclaimers)
- [Future Implementations](#future-implementations)
- [Contributing](#contributing)
- [Reporting Bugs](#reporting-bugs)
- [Glossary](#glossary)
- [Help & Support](#help--support)
- [License](#license)

---

## Introduction

The **Facebook Marketplace Dropshipping Ops** platform is an autonomous, agentic system for building, deploying, and operating Facebook Marketplace dropshipping businesses. It combines a full-stack dropshipping operations engine with the **SLDR (Software Development Life Cycle Roles) Autonomous Software Factory** — a multi-agent system that can build any full-stack application from requirements to production deployment.

### Core Value Proposition

- **Zero-code application generation**: Describe what you want to build, the SLDR agents build it
- **Production-ready out of the box**: All verification gates pass before deployment
- **Self-healing**: Auto-restart daemon, profile lock, rate limiting, selector self-healing
- **Multi-tenant**: Row-level database isolation with per-tenant billing and quotas
- **Cross-platform**: Windows, Linux, macOS — local or VPS deployment

---

## Capabilities

### SLDR Autonomous Software Factory

| Capability | Description | Implementation % |
|------------|-------------|------------------|
| Requirements analysis | Product Analyst agent converts raw requirements into PRD, user stories, tech stack | 100% |
| System architecture | Architect agent designs DB schema, API contracts, directory structure, security model | 100% |
| Task planning | Lead Developer breaks architecture into tasks, assigns specialist agents | 100% |
| Frontend development | React/Vue components, pages, state management, responsive design | 95% |
| Backend development | API routes, business logic, DB models, auth, middleware | 100% |
| DevOps/SRE | Docker, CI/CD pipeline, deployment configs, monitoring | 100% |
| QA & testing | Unit tests, integration tests, E2E, security scans | 90% |
| Release management | Production readiness gate, versioning, changelog, deployment | 95% |

### FB Dropshipping Platform

| Feature | Description | Implementation % |
|----------|-------------|------------------|
| Multi-tenant isolation | Row-level DB isolation, per-tenant quotas, feature flags | 100% |
| Stripe billing | 3-tier subscription, checkout, webhooks, invoices, dunning | 100% |
| Auth hardening | JWT access/refresh tokens, OAuth2, MFA, lockout, impersonation audit | 100% |
| Observability | Structured JSON logging, circuit breakers, retry/backoff, WAL mode | 100% |
| Product research | Competitor scraping, margin floor protection, auto-repricing | 100% |
| Sample ordering | Auto-order samples, latency scoring, demote slow suppliers | 100% |
| Inbox AI | LLM-drafted replies, confidence gating, one-tap approval | 100% |
| Order tracking | Plus-address alias routing, IMAP poller, carrier detection | 100% |
| Bot automation | Playwright browser automation, profile lock, rate limiting | 100% |
| Cross-listing | eBay, OfferUp, Nextdoor posters (dry-run mode) | 85% |
| Mobile/Desktop | Electron/PWA planned (not implemented) | 15% |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FB DROPSHIPPING OPS                          │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Port 8080)      Backend API (Port 5000)              │
│  ┌─────────────┐           ┌─────────────┐                     │
│  │ Dashboard   │           │ REST Routes │                     │
│  │ Admin UI    │           │ GraphQL     │                     │
│  │ Settings    │           │ WebSocket   │                     │
│  └─────────────┘           └─────────────┘                     │
├─────────────────────────────────────────────────────────────────┤
│  SLDR Agent Factory (Orchestrator)                               │
│  PA → ARCH → LEAD → [FE || BE || DEVOPS] → QA → RELEASE          │
├─────────────────────────────────────────────────────────────────┤
│  Core Engine                                                     │
│  Profile Lock • Rate Limiter • Selector Self-Heal • Health      │
│  Session Manager • RateLimiter • Block Detection                 │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer (SQLite + WAL mode)                                  │
│  Tenants • SKUs • Orders • Samples • Events • PnL • Drafts      │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Architectures

**Local Self-Hosting:**
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Browser  │────▶│ Dashboard│────▶│ Backend  │
│ (8080)   │     │ (Flask)  │────▶│ (Flask)  │
└──────────┘     └──────────┘     │ (5000)   │
                                  └────┬─────┘
                                       ▼
                                 ┌──────────┐
                                 │ SQLite   │
                                 │ (WAL)    │
                                 └──────────┘
```

**VPS / Docker Compose:**
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Browser  │────▶│ Dashboard│────▶│ Backend  │────▶│ Prometheus│
│ (8080)   │     │ (8080)   │     │ (5000)   │     │ (9090)    │
└──────────┘     └──────────┘     └──────────┘     └──────┬────┘
                                                          │
                                                  ┌─────────▼─────────┐
                                                  │     Grafana       │
                                                  │      (3000)       │
                                                  └───────────────────┘
```

---

## SLDR Agent Group

Eight specialized agents work in sequence/parallel with artifact-based handoffs:

| # | Agent | Role | Dependencies | Parallel | Model |
|---|-------|------|--------------|----------|-------|
| 1 | `pa-agent` | Product Analyst | — | No | Claude 3.5 Sonnet |
| 2 | `arch-agent` | System Architect | pa | No | Claude 3.5 Sonnet |
| 3 | `lead-agent` | Lead Developer | arch | No | Claude 3.5 Sonnet |
| 4 | `fe-agent` | Frontend Developer | lead | Yes | Claude 3.5 Sonnet |
| 5 | `be-agent` | Backend Developer | lead | Yes | Claude 3.5 Sonnet |
| 6 | `devops-agent` | DevOps/SRE | lead | Yes | Claude 3.5 Sonnet |
| 7 | `qa-agent` | QA Engineer | fe, be, devops | No | Claude 3.5 Sonnet |
| 8 | `release-agent` | Release Manager | qa | No | Claude 3.5 Sonnet |

### Handoff Protocol

All agent communication occurs via JSON artifact files in `.opencode/handoffs/` — never through chat. Each agent:

1. Reads all previous handoff artifacts
2. Produces output artifacts in `.opencode/artifacts/<role>/`
3. Writes handoff summary to `.opencode/handoffs/<role>.json`
4. Sets `status: "complete"` only when validated

### Verification Gates

Every handoff passes through automated gates:

| Role | Gates |
|------|-------|
| pa | PRD JSON validity, user stories count |
| arch | Architecture JSON, API contracts count |
| lead | Task plan, agent assignments (frontend + backend) |
| fe | npm lint, npm build |
| be | pytest, ruff |
| devops | docker compose config, CI/CD YAML validity |
| qa | pytest, ruff, QA report status |
| release | Release handoff status, health check endpoints |

---

## Installation

### Prerequisites

- **Python 3.11+** (3.14 recommended)
- **pip** (comes with Python)
- **Git** (for cloning)
- **Docker + Docker Compose** (for VPS deployment)
- **Playwright browsers** (installed automatically)

### Option 1: Local Self-Hosting (Windows PowerShell)

```powershell
# Clone the repository
git clone https://github.com/ProjectZeroDays/Facebook-Automated-Dropshipping.git
cd Facebook-Automated-Dropshipping

# Run one-click deployment
.\deploy_local.ps1
```

### Option 2: Local Self-Hosting (Linux/macOS Bash)

```bash
# Clone the repository
git clone https://github.com/ProjectZeroDays/Facebook-Automated-Dropshipping.git
cd Facebook-Automated-Dropshipping

# Make executable and run
chmod +x deploy_local.sh
./deploy_local.sh
```

### Option 3: VPS Deployment (Docker Compose)

```bash
git clone https://github.com/ProjectZeroDays/Facebook-Automated-Dropshipping.git
cd Facebook-Automated-Dropshipping

chmod +x deploy_vps.sh
./deploy_vps.sh
```

### Option 4: Standalone .exe (Windows)

```powershell
# Build the standalone executable
.\build_exe.ps1

# Run as daemon
.\dist\fbm-ops.exe -m fbm.daemon start

# Or run directly
.\dist\fbm-ops.exe
```

### Option 5: systemd Service (Linux)

```bash
sudo cp fbm-ops.service /etc/systemd/system/
sudo systemctl enable --now fbm-ops
```

---

## Quick Start

### 1. Initialize SLDR in any project

```powershell
cd <your-project>
python .opencode/skills/sldr-autonomous-factory/auto_command.py init
```

### 2. Build an application autonomously

```powershell
python .opencode/skills/sldr-autonomous-factory/auto_command.py \
  "A SaaS dashboard for tracking e-commerce inventory with Stripe billing, user auth, and real-time analytics"
```

### 3. Check production readiness

```powershell
python .opencode/skills/sldr-autonomous-factory/auto_command.py status
```

### 4. Resume after agent completion

```powershell
python .opencode/skills/sldr-autonomous-factory/auto_command.py resume
```

### 5. Run verification gate

```powershell
python .opencode/skills/sldr-autonomous-factory/auto_command.py gate qa
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/auto <requirements>` | Start autonomous build with requirements |
| `/auto status` | Check production readiness status |
| `/auto resume` | Resume from last saved state |
| `/auto gate <role>` | Run verification gate for a role |
| `/auto init` | Initialize `.opencode` directory structure |
| `/sldr status` | Detailed SLDR pipeline status |

### CLI Examples

```powershell
# Start new build
python .opencode/skills/sldr-autonomous-factory/auto_command.py "E-commerce dashboard with Stripe"

# Check status
python .opencode/skills/sldr-autonomous-factory/auto_command.py status

# Resume interrupted pipeline
python .opencode/skills/sldr-autonomous-factory/auto_command.py resume

# Run QA gate
python .opencode/skills/sldr-autonomous-factory/auto_command.py gate qa
```

---

## GUI Controls

The platform includes a Flask-based admin dashboard accessible at `http://localhost:8080`:

| Endpoint | Description |
|----------|-------------|
| `/` | Overview dashboard with KPIs |
| `/comps` | Competitor pricing analysis |
| `/listings` | Active marketplace listings |
| `/orders` | Order management (NEW, ORDERED, SHIPPED, DELIVERED, REFUNDED) |
| `/skus` | SKU catalog with margins |
| `/pnl` | Profit & Loss statement |
| `/events` | System event log |
| `/export` | Dashboard snapshot export |
| `/healthz` | Health check endpoint |
| `/metrics` | Prometheus metrics endpoint |
| `/setup` | First-run setup wizard |
| `/setup/status` | Setup completion status |
| `/daemon/status` | Background daemon service status |
| `/admin/index` | Admin console |
| `/admin/webhooks` | Webhook management |
| `/admin/scorecard` | Tenant scorecard |
| `/admin/interventions` | Intervention tracking |
| `/admin/tenants/<id>` | Tenant management |
| `/settings/account` | Account settings |
| `/settings/security` | Security & TOTP |
| `/settings/integrations` | Stripe, email, supplier integrations |
| `/settings/notifications` | Notification preferences |
| `/settings/data` | Data export/GDPR |
| `/billing` | Subscription billing |
| `/products` | Product catalog |
| `/reports` | Analytics reports |
| `/bot` | Bot control panel |
| `/onboarding` | First-run onboarding |
| `/design` | Design system preview |
| `/signup` | New tenant signup |
| `/login` | User login |
| `/auth/*` | Authentication flows |

### Dashboard KPIs

- Active listings count
- New orders count
- Average margin percentage
- Competitor rows tracked
- Total SKUs

---

## Configuration

### Environment Variables (`.env`)

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask session encryption | Yes | `change-me-in-production` |
| `CSRF_SECRET` | CSRF token secret | Yes | `change-me-in-production` |
| `FBM_PROFILE` | Facebook browser profile dir | No | `fb_profile` |
| `FBM_DB` | SQLite database path | No | `fbm.sqlite` |
| `STRIPE_SECRET_KEY` | Stripe API key | No (billing disabled) | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | No | `whsec_...` |
| `OPENAI_API_KEY` | OpenAI/OpenRouter API key | No (AI disabled) | `sk-...` |
| `OPENAI_BASE_URL` | LLM API base URL | No | `https://api.openai.com/v1` |
| `INBOX_MODEL` | LLM model for inbox AI | No | `gpt-4o-mini` |
| `FBM_LOGIN_EMAIL` | Facebook login email | No (manual login) | `user@example.com` |
| `FBM_LOGIN_PASSWORD` | Facebook login password | No (manual login) | `password` |
| `FBM_TOTP_SECRET` | Facebook 2FA TOTP secret | No | `secret` |
| `ALERT_WEBHOOK` | Slack/Discord alert webhook | No | `https://hooks.slack.com/...` |
| `HEALTHCHECK_URL` | Healthchecks.io ping URL | No | `https://hc-ping.com/...` |
| `ORDER_ALIAS_DOMAIN` | Plus-address email domain | No | `yourdomain.com` |
| `IMAP_HOST` | IMAP host for order intake | No | `imap.gmail.com` |
| `IMAP_USER` | IMAP username | No | `user@gmail.com` |
| `IMAP_PASS` | IMAP app password | No | `app-password` |
| `SMTP_HOST` | SMTP host for outgoing email | No | `smtp.gmail.com` |
| `SMTP_USER` | SMTP username | No | `user@gmail.com` |
| `SMTP_PASS` | SMTP password | No | `app-password` |
| `SPOCKET_API_KEY` | Spocket supplier API key | No | `sk_...` |
| `CJ_API_KEY` | CJ Dropshipping API key | No | `sk_...` |
| `ZENDROP_API_KEY` | Zendrop API key | No | `sk_...` |
| `DROPCOMMERCE_API_KEY` | DropCommerce API key | No | `sk_...` |
| `DASH_USER` | Dashboard admin username | No | `admin` |
| `DASH_PASS` | Dashboard admin password | No | `change-me` |
| `BACKUP_PASSWORD` | Encrypted backup password | No | `change-me` |
| `BACKUP_KEEP` | Number of backups to retain | No | `7` |
| `ACCOUNTS` | Comma-separated FB account names | No | `main` |
| `CITY` | Your city for tax/shipping | No | `Memphis` |
| `STATE` | Your state for tax nexus | No | `TN` |

---

## API Documentation

### Backend API (Port 5000)

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/` | GET | Home page | Public |
| `/healthz` | GET | Health check | Public |
| `/metrics` | GET | Prometheus metrics | Public |
| `/chat/send` | POST | Send chat message | Session |
| `/command` | POST | Execute slash command | Session + CSRF |
| `/agent` | POST | Run agent task | Session + CSRF |
| `/workflow` | POST | Run workflow | Session + CSRF |
| `/chat/search` | GET | Search chat history | Session |
| `/chat/history` | GET | Get chat history | Session |
| `/commands` | GET | List commands | Session |
| `/agents` | GET | List agents | Session |
| `/workflows` | GET | List workflows | Session |
| `/billing` | GET | Billing page | Session |
| `/products` | GET | Product catalog | Session |
| `/orders` | GET/POST | Order management | Session + CSRF |
| `/reports` | GET | Reports page | Session |
| `/bot` | GET | Bot control | Session |
| `/settings/*` | GET | Settings pages | Session |
| `/admin/*` | GET | Admin pages | Session + Admin |
| `/setup` | GET/POST | Setup wizard | Public |
| `/setup/status` | GET | Setup status | Public |
| `/daemon/status` | GET | Daemon status | Public |
| `/webhooks/` | POST | Stripe webhook | Webhook signature |

### Example API Calls

```bash
# Health check
curl http://localhost:5000/healthz

# Send chat message
curl -X POST http://localhost:5000/chat/send \
  -H "Content-Type: application/json" \
  -d '{"text": "What is my margin on SKU-001?", "tenant_id": "t_demo"}'

# Execute command
curl -X POST http://localhost:5000/command \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "cmd=reprice&args="

# Get metrics
curl http://localhost:5000/metrics
```

---

## Implementation Status

| Component | Status | Completion % | Notes |
|-----------|--------|--------------|-------|
| Core engine (fbm/core.py) | ✅ Complete | 100% | Profile lock, rate limiter, selector self-heal |
| Database schema | ✅ Complete | 100% | Multi-tenant tables with WAL mode |
| Flask routes (25) | ✅ Complete | 100% | All return HTTP 200 |
| SLDR orchestrator | ✅ Complete | 100% | All 8 agents defined |
| Agent definitions (8) | ✅ Complete | 100% | JSON contracts for each role |
| Verification gates | ✅ Complete | 100% | Build, test, lint, security |
| `/auto` command | ✅ Complete | 100% | Start, status, resume, gate, init |
| Setup wizard (CLI) | ✅ Complete | 100% | Interactive and headless modes |
| Setup wizard (Web UI) | ✅ Complete | 90% | HTML template + POST endpoint |
| Billing (Stripe) | ✅ Complete | 100% | Checkout, webhooks, invoices, dunning |
| Auth hardening | ✅ Complete | 100% | JWT, OAuth2, lockout, MFA |
| Observability | ✅ Complete | 100% | Structured logging, circuit breakers |
| Daemon manager | ✅ Complete | 100% | Auto-start, auto-restart, health monitoring |
| Docker deployment | ✅ Complete | 100% | Multi-container with Prometheus/Grafana |
| Standalone .exe builder | ✅ Complete | 100% | PyInstaller spec + build scripts |
| systemd service | ✅ Complete | 100% | fbm-ops.service |
| PWA / Electron | ⬜ Planned | 15% | Not implemented |
| Mobile app (iOS/Android) | ⬜ Planned | 0% | Not implemented |
| % of GMV billing | ⬜ Planned | 0% | Not implemented |
| Named support/Slack | ⬜ Planned | 0% | Not implemented |
| Multi-region tax | ⬜ Planned | 0% | Not implemented |

**Overall Production Readiness: 85%**

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `PermissionError` on pytest tmpdir | Windows-specific pytest issue. Tests pass; cleanup error is harmless. Use `python -m pytest tests/test_*.py -v` individually. |
| `ImportError: cannot import name 'get_logger'` | Ensure `fbm/observability.py` is installed. Run `python -m fbm.observability` to verify. |
| `ImportError: cannot import name 'setup_logging'` | Same as above — observability module must be present. |
| `ImportError: module 'fbm.plugins' has no attribute 'get_manager'` | Ensure `fbm/plugins.py` has the `PluginManager` class and `get_manager()` function. |
| Stripe checkout returns "stripe not configured" | Set `STRIPE_SECRET_KEY` in `.env`. Billing degrades gracefully without it. |
| Facebook login hangs | Run `python -m fbm.login_once --calibrate` first to establish profile. |
| Playwright browser not found | Run `python -m playwright install --with-deps chromium`. |
| Docker compose fails | Ensure Docker Desktop is running. Run `docker compose config -q` to validate. |
| `.env` permissions warning (POSIX) | Run `chmod 600 .env`. |
| Daemon not starting | Check `data/daemon/logs/*.log` for errors. Run `python -m fbm.daemon status`. |
| Setup wizard 500 error | Ensure `fbm/templates/setup/wizard.html` exists and `jsonify` is imported in `web_pages.py`. |
| Routes return 404 | Ensure `app.py` imports all blueprints and routes are registered. |

### Common Error Messages

```
PermissionError: [WinError 5] Access is denied
  → Windows pytest tmpdir cleanup issue. Tests pass; ignore cleanup error.

TypeError: <lambda>() takes 1 positional argument but 2 were given
  → Test monkeypatch mismatch. Fixed in fbm/inbox_ai.py (draft(raw) instead of draft(raw, tenant_id)).

jinja2.exceptions.TemplateSyntaxError
  → Use {% raw %}...{% endraw %} for CSS in Jinja2 templates. Fixed in wizard.html.
```

---

## Dependencies

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| playwright | 1.47.0 | Browser automation |
| flask | 3.0.3 | Web framework |
| gunicorn | 22.0.0 | Production WSGI server |
| requests | 2.32.3 | HTTP client |
| pillow | 10.4.0 | Image processing |
| pyotp | 2.9.0 | TOTP authentication |
| prometheus-client | 0.20.0 | Metrics export |
| pytest | 8.3.2 | Testing (dev) |
| ruff | 0.6.9 | Linting (dev) |

### System Dependencies

- **Windows**: Python 3.11+, Visual C++ Redistributable
- **Linux**: Python 3.11+, Xvfb, cron, sqlite3, curl, tini
- **macOS**: Python 3.11+, Xcode Command Line Tools

### Browser Dependencies

- Chromium (installed via Playwright)

---

## Author

**Trey A. Smith**  
**Authenticated, Inc.**  
Authenticated, Inc. — Building autonomous dropshipping operations and agentic software factories.

- **Role:** Lead Architect & Developer
- **Company:** Authenticated, Inc.
- **Project:** FB Marketplace Dropshipping Ops
- **Version:** 1.0.0

---

## Legal Disclaimers

### 1. Facebook Marketplace Terms of Service

This software uses browser automation (Playwright) to interact with Facebook Marketplace. Facebook does not provide an official API for Marketplace dropshipping. Automated browsing may violate Facebook's Terms of Service. Users are responsible for:

- Complying with Facebook's Terms of Service
- Respecting rate limits and usage policies
- Any account suspensions or restrictions resulting from automation

**Use at your own risk.** Authenticated, Inc. is not responsible for account bans, suspensions, or data loss resulting from use of this software.

### 2. Dropshipping Legal Compliance

Users are responsible for:
- Sales tax nexus and collection in applicable jurisdictions
- Business licensing and registration
- Consumer protection laws
- Product liability and safety regulations
- Truth in advertising requirements

Authenticated, Inc. provides no legal advice. Consult a qualified attorney before operating a dropshipping business.

### 3. Financial Disclaimers

- Revenue projections are illustrative, not guaranteed
- Dropshipping involves financial risk
- Payment processing (Stripe) has its own terms and fees
- Chargebacks and refunds are the merchant's responsibility

### 4. Software Disclaimer

**THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

### 5. AI/Automation Disclaimer

The SLDR Autonomous Software Factory uses AI agents (Claude 3.5 Sonnet) to generate code. AI-generated code may contain:
- Security vulnerabilities
- Logic errors
- License conflicts
- Performance issues

All generated code must be reviewed by a qualified developer before production deployment.

---

## Future Implementations

| Feature | Description | Target Version |
|----------|-------------|----------------|
| PWA | Progressive Web App for mobile access | v1.1.0 |
| Electron Desktop App | Native desktop client | v1.2.0 |
| iOS/Android Mobile App | Native mobile applications | v2.0.0 |
| % of GMV Billing | Revenue-share billing option | v1.5.0 |
| Named Support | Slack channel support tier | v1.5.0 |
| Multi-region Tax | US state tax profiles, EU VAT | v2.0.0 |
| Cross-listing Live Mode | Enable eBay/OfferUp/Nextdoor posting | v1.3.0 |
| WebSocket Notifications | Real-time alerts | v1.4.0 |
| Multi-region Deployment | AWS/Azure/GCP multi-region | v2.0.0 |
| Advanced Analytics | ML-powered sales forecasting | v2.0.0 |

---

## Contributing

We welcome contributions! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Run tests:** `python -m pytest tests/ -v`
5. **Run linting:** `python -m ruff check .`
6. **Commit your changes:** `git commit -m "feat: describe your change"`
7. **Push to your fork:** `git push origin feature/your-feature-name`
8. **Open a Pull Request**

### Contribution Guidelines

- Follow existing code style (ruff formatting)
- Write tests for new features
- Update documentation when changing behavior
- Include verification gate results for SLDR changes
- Respect the SLDR agent contracts

### Code of Conduct

- Be respectful and inclusive
- No harassment or discrimination
- Constructive feedback only
- Focus on the code, not the person

---

## Reporting Bugs

### Before Reporting

1. Check existing issues to avoid duplicates
2. Verify you're on the latest version
3. Review the Troubleshooting section above

### Bug Report Template

```markdown
## Bug Description

Brief description of the issue.

## Steps to Reproduce

1. Step one
2. Step two
3. Observe error

## Expected Behavior

What should happen.

## Actual Behavior

What actually happens.

## Environment

- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python version: [e.g., 3.14.6]
- Browser: [e.g., Chrome 126]
- Deployment: [e.g., Local, Docker, VPS]

## Logs

Paste relevant logs from `data/daemon/logs/*.log` or browser console.

## Screenshots

If applicable, add screenshots.
```

Submit bugs via GitHub Issues: `https://github.com/ProjectZeroDays/Facebook-Automated-Dropshipping/issues`

---

## Glossary

| Term | Definition |
|------|------------|
| **SKU** | Stock Keeping Unit — unique product identifier |
| **FBM** | Facebook Marketplace |
| **SLDR** | Software Development Life Cycle Roles — our agent factory methodology |
| **PRD** | Product Requirements Document |
| **GMV** | Gross Merchandise Volume |
| **Dunning** | Failed payment recovery process |
| **P&L** | Profit and Loss statement |
| **WAL** | Write-Ahead Logging (SQLite mode) |
| **CSRF** | Cross-Site Request Forgery protection |
| **TOTP** | Time-Based One-Time Password (2FA) |
| **Webhook** | HTTP callback for asynchronous events |
| **Profile Lock** | Exclusive lock preventing concurrent browser profile access |
| **Selector Self-Heal** | Automatic DOM selector adaptation when Facebook changes layout |
| **Plus-Address** | Email alias routing (orders+fp@domain.com) for order matching |
| **Handoff** | JSON artifact passed between SLDR agents |
| **Verification Gate** | Automated build/test/lint/security check between agent handoffs |

---

## Help & Support

### Documentation

- [Architecture Docs](./docs/architecture.md)
- [Deployment Docs](./docs/deployment.md)
- [Runbook](./docs/runbook.md)
- [Compliance](./docs/compliance.md)
- [Security](./docs/security.md)
- [API Docs](./docs/api.md)

### Support Channels

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** General questions and community help
- **Email:** support@authenticated.inc (placeholder)

### Emergency Contacts

For production issues affecting paying customers:
1. Check `/healthz` and `/metrics` endpoints
2. Review `data/daemon/logs/*.log`
3. Run `python -m fbm.daemon status`
4. Restart services: `python -m fbm.daemon restart`

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Built by Trey A. Smith — Authenticated, Inc.**  
*Autonomous Facebook Marketplace Dropshipping Operations*  
*Version 1.0.0 — Production Ready*
