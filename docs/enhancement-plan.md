# Enhancement Plan — Autonomous Features, Workflows, Agents, MCPs, Plugins

## Remaining stubs to harden
- actions, whisper, download_model, bugreport, selfheal, updater, crosslist_post,
  insights, inbox, inbox_poller, google, payments, drip, onboarding_emails,
  emailcopy, adminroutes, tenants, autovars.

## New autonomous features
1. Plugin system (fbm/plugins.py) — load third-party extensions from plugins/.
2. Command registry (fbm/commands.py) — slash commands for CLI and chatbot.
3. Workflow engine (fbm/workflows.py) — composable pipelines with retries.
4. Agent framework (fbm/agents.py) — specialized subagents (scraper, copy, support).
5. MCP integration (fbm/mcp_client.py) — done.
6. Self-healing loop (enhanced selfheal.py).
7. Auto-scaling accounts (accounts.py already has load balancing).
8. Predictive repricing (reprice.py ML hooks).

## MCPs to add
- filesystem, github, sqlite, fetch, brave-search, slack.

## Plugins/extensions
- AutoDS bridge, Spocket bridge, CJ bridge, n8n bridge.

## Custom commands (slash)
- /publish, /renew, /recycle, /scrape, /reprice, /status, /backup, /restore.

## Subagents
- research-agent, copy-agent, support-agent, ops-agent.

## Security hardening
- CSRF tokens, input validation, SQL parameterization (already), XSS escaping,
  secret rotation, audit logging, rate limiting (already).

## Implementation order
1. Implement all stubs with real logic.
2. Add plugin + command + workflow + agent frameworks.
3. Wire MCP client into chatbot and actions.
4. Add security middleware (CSRF, headers, validation).
5. Refactor, test, scan vulnerabilities.
