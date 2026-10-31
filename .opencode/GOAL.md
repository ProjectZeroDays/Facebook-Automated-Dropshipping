# FB Dropshipper — Autonomous Goal (v1.2.0)

## Title
Reach production-ready autonomous FB Marketplace dropshipping with full CI/CD and standalone EXE.

## Metric
- All 7 expanded regression tests passing (imports, trial, admin, setup wizard, routes, billing contract, demo-check) ✅
- 23/24 GET routes passing (only /admin/dashboard 302 — expected redirect) ✅
- GitHub repo `ProjectZeroDays/Facebook-Automated-Dropshipping` at `v1.2.0` ✅
- Standalone EXE build pipeline (`build-exe.yml`) + deploy pipeline (`deploy-cloud.yml`) ✅
- Skills installed globally + per-project (~700) ✅
- SLDR autonomous factory skill installed (`sldr-autonomous-factory`) ✅

## Verification (before declaring done)
1. `python tests/test_expanded.py` → 7/7 pass
2. `python tests/test_comprehensive.py` → 4/4 pass
3. `git log --oneline -3` confirms `v1.2.0`
4. `/trial` POST with CSRF → 200 + `ok: true`
5. `/setup` creates admin → `verify_admin` = True
6. `.github/workflows/deploy-cloud.yml` exists
7. `release-exe.ps1` exists

## Deadline
Achieved at v1.2.0 (current session).

## Autonomy Status
- `/never-ask` active
- `/swarm` active (8 SLDR agents defined)
- `/auto` command registered (`/auto init/status/resume/gate`)
