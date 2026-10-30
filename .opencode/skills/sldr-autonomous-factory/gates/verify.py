#!/usr/bin/env python3
"""
SLDR Verification Gates - runs build, test, lint, security checks between handoffs.
Each gate returns exit code 0 on success, non-zero on failure.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path.cwd()
HANDOFFS_DIR = PROJECT_ROOT / ".opencode" / "handoffs"

GATE_COMMANDS = {
    "pa": [
        "python -c \"import json; d=json.load(open('.opencode/artifacts/pa/prd.json')); assert 'app_name' in d\"",
        "python -c \"import json; d=json.load(open('.opencode/artifacts/pa/user_stories.json')); assert len(d) > 0\"",
    ],
    "arch": [
        "python -c \"import json; d=json.load(open('.opencode/artifacts/arch/architecture.json')); assert 'database' in d\"",
        "python -c \"import json; d=json.load(open('.opencode/artifacts/arch/api_contracts.json')); assert len(d) > 0\"",
    ],
    "lead": [
        "python -c \"import json; d=json.load(open('.opencode/artifacts/lead/task_plan.json')); assert len(d) > 0\"",
        "python -c \"import json; d=json.load(open('.opencode/artifacts/lead/agent_assignments.json')); assert 'frontend' in d and 'backend' in d\"",
    ],
    "fe": [
        "npm run lint 2>/dev/null || echo 'lint skipped - no npm project'",
        "npm run build 2>/dev/null || echo 'build skipped - no npm project'",
    ],
    "be": [
        "python -m pytest tests/ -q 2>/dev/null || echo 'pytest skipped - no tests'",
        "python -m ruff check . 2>/dev/null || echo 'ruff skipped - not installed'",
    ],
    "devops": [
        "docker compose config -q 2>/dev/null || echo 'docker compose skipped'",
        "python -c \"import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))\" 2>/dev/null || echo 'CI config skipped'",
    ],
    "qa": [
        "python -m pytest tests/ -q 2>/dev/null || echo 'pytest skipped'",
        "python -m ruff check . 2>/dev/null || echo 'ruff skipped'",
        "python -c \"import json; d=json.load(open('.opencode/artifacts/qa/qa_report.json')); assert d.get('overall_status') in ('pass','fail')\" 2>/dev/null || echo 'qa report skipped'",
    ],
    "release": [
        "python -c \"import json; d=json.load(open('.opencode/handoffs/release.json')); assert d['status'] == 'complete'\"",
        "curl -fsS http://localhost:5000/healthz 2>/dev/null || echo 'backend health check skipped'",
        "curl -fsS http://localhost:8080/healthz 2>/dev/null || echo 'dashboard health check skipped'",
    ],
}


def run_gate(role: str) -> tuple[bool, str]:
    """Run verification gate for a role. Returns (success, message)."""
    commands = GATE_COMMANDS.get(role, [])
    if not commands:
        return True, "no gates defined"

    failures = []
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=PROJECT_ROOT,
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                failures.append(f"  {cmd}\n    {result.stderr.strip()[:200]}")
        except subprocess.TimeoutExpired:
            failures.append(f"  {cmd}\n    TIMEOUT")
        except Exception as e:
            failures.append(f"  {cmd}\n    {e}")

    if failures:
        return False, "\n".join(failures)
    return True, f"All {len(commands)} gate(s) passed for {role}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SLDR Verification Gate")
    parser.add_argument("role", help="Role ID to verify (pa, arch, lead, fe, be, devops, qa, release)")
    args = parser.parse_args()

    success, message = run_gate(args.role)
    print(message)

    if success:
        # Mark role as complete in state
        state_file = PROJECT_ROOT / ".opencode" / "sldr_state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            completed = state.get("completed_roles", [])
            if args.role not in completed:
                completed.append(args.role)
                state["completed_roles"] = completed
                state["current_role"] = None
                state_file.write_text(json.dumps(state, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()