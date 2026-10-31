HEAL-2026-10-30 /trial
Pattern-Key: csrf_token-context-variable-vs-callable
Recurrence-Count: 1
Root-Cause: `fbm/templates/trial.html` used `{{ csrf_token() }}` (call syntax) but `csrf_token` is a pre-evaluated string injected by `inject_globals` in `app.py`, not a callable in Jinja context.
Fix-Verified: Changed to `{{ csrf_token }}` (variable reference); `/trial` GET returns 200 and POST with CSRF token returns 200 with `{ok: true}`.
Evidence: `python tests/test_expanded.py` → PASS trial_full_flow (4/4)
Proof: `git show f71c17e` (commit fixing trial route + template)
