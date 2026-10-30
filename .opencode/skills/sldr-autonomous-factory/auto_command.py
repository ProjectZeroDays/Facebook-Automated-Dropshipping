#!/usr/bin/env python3
"""
/auto Command - SLDR Autonomous Software Factory Entry Point

Analyzes current app state, picks up where it left off, prompts for missing info,
and runs the SLDR pipeline to completion.

Usage:
  /auto <requirements>     - Start new build with requirements
  /auto status             - Check current production readiness
  /auto resume             - Resume from last saved state
  /auto gate <role>        - Run verification gate for a role
  /auto init               - Initialize .opencode directory structure
"""

from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path.cwd()
OPENACE_DIR = PROJECT_ROOT / ".opencode"
HANDOFFS_DIR = OPENACE_DIR / "handoffs"
ARTIFACTS_DIR = OPENACE_DIR / "artifacts"
STATE_FILE = OPENACE_DIR / "sldr_state.json"

# Add orchestrator to path
sys.path.insert(0, str(PROJECT_ROOT / ".opencode" / "skills" / "sldr-autonomous-factory"))
from orchestrator import SLDROrchestrator, SLDR_PIPELINE, ROLE_DESCRIPTIONS


def init_project():
    """Initialize .opencode directory structure for SLDR."""
    for d in [OPENACE_DIR, HANDOFFS_DIR, ARTIFACTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        for role_id, _, _, _, _ in SLDR_PIPELINE:
            (ARTIFACTS_DIR / role_id).mkdir(parents=True, exist_ok=True)

    # Create initial state if not exists
    if not STATE_FILE.exists():
        initial_state = {
            "run_id": None,
            "app_description": None,
            "current_role": None,
            "completed_roles": [],
            "failed_roles": [],
            "artifacts": {},
            "started_at": None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        STATE_FILE.write_text(json.dumps(initial_state, indent=2))

    print(f"Initialized .opencode/ structure at {PROJECT_ROOT}")
    print("Run /auto <requirements> to start building.")


def show_status():
    """Show current production readiness status."""
    orch = SLDROrchestrator()
    state = orch.load_state()

    print("\n" + "=" * 60)
    print("SLDR PRODUCTION READINESS STATUS")
    print("=" * 60)

    if not state.get("run_id"):
        print("\nStatus: NOT STARTED")
        print("No SLDR run has been initiated.")
        print("\nTo start: /auto <your app requirements>")
        return

    completed = state.get("completed_roles", [])
    current = state.get("current_role")
    total = len(SLDR_PIPELINE)

    print(f"\nRun ID: {state['run_id']}")
    print(f"App: {state.get('app_description', 'N/A')}")
    print(f"Progress: {len(completed)}/{total} roles completed")
    print(f"Current role: {current if current else 'None (paused)'}")

    print("\nRole Status:")
    for role_id, agent_name, deps, parallel, _ in SLDR_PIPELINE:
        status_icon = ""
        if role_id in completed:
            status_icon = "[OK]"
        elif role_id == current:
            status_icon = "[RUN]"
        elif all(d in completed for d in deps):
            status_icon = "[READY]"
        else:
            status_icon = "[BLOCKED]"
        print(f"  {status_icon} {role_id.upper():8} - {agent_name}")

    # Production readiness
    ready_for_prod = "release" in completed
    print(f"\nProduction Ready: {'YES' if ready_for_prod else 'NO'}")

    if not ready_for_prod:
        remaining = [r[0] for r in SLDR_PIPELINE if r[0] not in completed]
        print(f"Remaining roles: {', '.join(r.upper() for r in remaining)}")


def start_or_resume(requirements: str = None, resume: bool = False):
    """Start new SLDR run or resume existing."""
    orch = SLDROrchestrator()

    if resume:
        print("Resuming SLDR pipeline...")
        orch.run_pipeline(resume=True)
    else:
        if not requirements:
            requirements = input("Enter your application requirements: ").strip()
            if not requirements:
                print("ERROR: Requirements are required to start.")
                return
        print(f"Starting SLDR pipeline for: {requirements}")
        orch.run_pipeline(app_description=requirements, resume=False)


def run_gate(role: str):
    """Run verification gate for a specific role."""
    orch = SLDROrchestrator()
    ok = orch.run_verification_gate(role)
    if ok:
        state = orch.load_state()
        orch.mark_role_complete(role, state)
        print(f"\nGate PASSED for {role}. Ready for next role.")
    else:
        print(f"\nGate FAILED for {role}. Fix issues and re-run.")


def main():
    if len(sys.argv) < 2:
        print("Usage: /auto <command> [args]")
        print("  /auto <requirements>   - Start new build")
        print("  /auto status           - Check production readiness")
        print("  /auto resume           - Resume from last state")
        print("  /auto gate <role>      - Run verification gate")
        print("  /auto init             - Initialize .opencode structure")
        return

    command = sys.argv[1]

    if command == "init":
        init_project()
    elif command == "status":
        show_status()
    elif command == "resume":
        start_or_resume(resume=True)
    elif command == "gate":
        if len(sys.argv) < 3:
            print("Usage: /auto gate <role>")
            return
        run_gate(sys.argv[2])
    else:
        # Treat as requirements for new build
        requirements = " ".join(sys.argv[1:])
        start_or_resume(requirements=requirements)


if __name__ == "__main__":
    main()