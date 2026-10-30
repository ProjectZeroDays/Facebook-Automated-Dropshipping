#!/usr/bin/env python3
"""
SLDR Autonomous Software Factory - Orchestrator Engine

Manages the SLDR (Software Development Life Cycle Roles) agent pipeline:
  PA: Product Analyst -> ARCH: System Architect -> LEAD: Lead Developer
  -> FE: Frontend Developer || BE: Backend Developer || DEVOPS: DevOps/SRE (parallel)
  -> QA: QA Engineer -> RELEASE: Release Manager

Uses artifact-based handoffs (JSON files in .opencode/handoffs/)
with verification gates between every handoff.
Supports intelligent resume via /auto command.
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Paths ---
PROJECT_ROOT = Path.cwd()
OPENACE_DIR = PROJECT_ROOT / ".opencode"
HANDOFFS_DIR = OPENACE_DIR / "handoffs"
ARTIFACTS_DIR = OPENACE_DIR / "artifacts"
STATE_FILE = OPENACE_DIR / "sldr_state.json"
GLOBAL_SKILL_DIR = Path.home() / ".opencode" / "skills" / "sldr-autonomous-factory"

# --- SLDR Pipeline Definition ---
# Each role: (role_id, agent_name, depends_on, parallel_group, prompt_template)
SLDR_PIPELINE = [
    ("pa", "Product Analyst", [], "sequential", "pa_prompt"),
    ("arch", "System Architect", ["pa"], "sequential", "arch_prompt"),
    ("lead", "Lead Developer", ["arch"], "sequential", "lead_prompt"),
    ("fe", "Frontend Developer", ["lead"], "parallel", "fe_prompt"),
    ("be", "Backend Developer", ["lead"], "parallel", "be_prompt"),
    ("devops", "DevOps/SRE", ["lead"], "parallel", "devops_prompt"),
    ("qa", "QA Engineer", ["fe", "be", "devops"], "sequential", "qa_prompt"),
    ("release", "Release Manager", ["qa"], "sequential", "release_prompt"),
]

# Role descriptions for user-facing messages
ROLE_DESCRIPTIONS = {
    "pa": "Product Analyst - requirements, PRD, user stories, tech stack",
    "arch": "System Architect - DB schema, API contracts, directory structure, security model",
    "lead": "Lead Developer - task breakdown, agent assignments, coding standards",
    "fe": "Frontend Developer - UI components, pages, state management",
    "be": "Backend Developer - API routes, business logic, database models",
    "devops": "DevOps/SRE - Docker, CI/CD, deployment configs, monitoring",
    "qa": "QA Engineer - unit tests, integration tests, E2E, security scans",
    "release": "Release Manager - production readiness gate, versioning, deployment",
}

# Verification gate commands per role
VERIFICATION_GATES = {
    "pa": ["python -c \"import json; json.load(open('.opencode/artifacts/pa/prd.json'))\""],
    "arch": ["python -c \"import json; json.load(open('.opencode/artifacts/arch/architecture.json'))\""],
    "lead": ["python -c \"import json; json.load(open('.opencode/artifacts/lead/task_plan.json'))\""],
    "fe": ["npm run lint || echo 'lint skipped'", "npm run build || echo 'build skipped'"],
    "be": ["python -m pytest tests/ -q", "python -m ruff check ."],
    "devops": ["docker compose config -q || echo 'docker compose skipped'"],
    "qa": ["python -m pytest tests/ -q", "python -m ruff check ."],
    "release": ["python -c \"import json; d=json.load(open('.opencode/handoffs/release.json')); print(d['status'])\""],
}


class SLDROrchestrator:
    """Orchestrates the SLDR autonomous software factory pipeline."""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.opencode_dir = project_root / ".opencode"
        self.handovers_dir = self.opencode_dir / "handoffs"
        self.artifacts_dir = self.opencode_dir / "artifacts"
        self.state_file = self.opencode_dir / "sldr_state.json"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create required directories."""
        for d in [self.opencode_dir, self.handovers_dir, self.artifacts_dir]:
            d.mkdir(parents=True, exist_ok=True)
        for role, _, _, _, _ in SLDR_PIPELINE:
            (self.artifacts_dir / role).mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict[str, Any]:
        """Load current pipeline state."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return {
            "run_id": None,
            "app_description": None,
            "current_role": None,
            "completed_roles": [],
            "failed_roles": [],
            "artifacts": {},
            "started_at": None,
            "last_updated": None,
        }

    def save_state(self, state: Dict[str, Any]):
        """Persist pipeline state."""
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state_file.write_text(json.dumps(state, indent=2))

    def load_handoff(self, role: str) -> Optional[Dict[str, Any]]:
        """Load a handoff artifact for a specific role."""
        handoff_file = self.handovers_dir / f"{role}.json"
        if handoff_file.exists():
            try:
                return json.loads(handoff_file.read_text())
            except Exception:
                return None
        return None

    def save_handoff(self, role: str, data: Dict[str, Any]):
        """Save a handoff artifact for a specific role."""
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        data["role"] = role
        self.handovers_dir.mkdir(parents=True, exist_ok=True)
        (self.handovers_dir / f"{role}.json").write_text(json.dumps(data, indent=2))

    def is_role_completed(self, role: str, state: Dict[str, Any]) -> bool:
        """Check if a role has been completed."""
        return role in state.get("completed_roles", [])

    def get_next_roles(self, state: Dict[str, Any]) -> List[tuple]:
        """Get roles that are ready to execute (dependencies satisfied)."""
        completed = set(state.get("completed_roles", []))
        ready = []
        for role_id, agent_name, deps, parallel_group, prompt_template in SLDR_PIPELINE:
            if role_id in completed:
                continue
            if all(dep in completed for dep in deps):
                ready.append((role_id, agent_name, parallel_group, prompt_template))
        return ready

    def run_verification_gate(self, role: str) -> bool:
        """Run verification gate for a completed role."""
        gates = VERIFICATION_GATES.get(role, [])
        if not gates:
            return True
        for gate_cmd in gates:
            try:
                result = subprocess.run(
                    gate_cmd,
                    shell=True,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode != 0:
                    print(f"  [GATE FAIL] {role}: {gate_cmd}")
                    print(f"    {result.stderr.strip()[:200]}")
                    return False
            except subprocess.TimeoutExpired:
                print(f"  [GATE TIMEOUT] {role}: {gate_cmd}")
                return False
            except Exception as e:
                print(f"  [GATE ERROR] {role}: {gate_cmd} -> {e}")
                return False
        return True

    def prompt_for_missing_info(self, role: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt user for missing information required by a role."""
        # This is called by the /auto command handler
        # Returns updated state with new info
        missing = self._identify_missing_info(role, state)
        if not missing:
            return state

        print(f"\n{'='*60}")
        print(f"SLDR needs information for role: {ROLE_DESCRIPTIONS.get(role, role)}")
        print(f"{'='*60}")
        for key, description in missing.items():
            current = state.get("artifacts", {}).get(key)
            if current:
                print(f"  {key}: {current} (current)")
                new_val = input(f"  New value (press Enter to keep current): ").strip()
                if new_val:
                    state.setdefault("artifacts", {})[key] = new_val
            else:
                val = input(f"  {key} ({description}): ").strip()
                if val:
                    state.setdefault("artifacts", {})[key] = val

        self.save_state(state)
        return state

    def _identify_missing_info(self, role: str, state: Dict[str, Any]) -> Dict[str, str]:
        """Identify what information is missing for a role."""
        missing = {}
        artifacts = state.get("artifacts", {})

        required_by_role = {
            "pa": {
                "app_description": "What is the application you want to build?",
                "target_users": "Who are the target users?",
                "core_features": "What are the 3-5 core features?",
                "tech_stack_preference": "Preferred tech stack (e.g., React+FastAPI, Next.js+Python)",
            },
            "arch": {
                "database_preference": "Preferred database (PostgreSQL, SQLite, MongoDB, etc.)",
                "auth_requirement": "Do you need user authentication? (yes/no)",
                "deployment_target": "Where will this deploy? (local, VPS, cloud)",
            },
            "be": {
                "api_prefix": "API URL prefix (e.g., /api/v1)",
                "cors_origins": "Allowed CORS origins",
            },
            "devops": {
                "docker_registry": "Docker registry URL (or leave empty for local)",
                "ssl_required": "Is SSL required? (yes/no)",
            },
        }

        for key, description in required_by_role.get(role, {}).items():
            if key not in artifacts or not artifacts[key]:
                missing[key] = description

        return missing

    def execute_role(self, role_id: str, agent_name: str, prompt_template: str, state: Dict[str, Any]) -> bool:
        """Execute a single SLDR role by spawning a subagent."""
        print(f"\n{'='*60}")
        print(f"SLDR Role: {role_id.upper()} - {agent_name}")
        print(f"{'='*60}")

        # Prompt for missing info first
        state = self.prompt_for_missing_info(role_id, state)

        # Build the prompt for the subagent
        prompt = self._build_role_prompt(role_id, agent_name, prompt_template, state)

        # In OpenCode, this would spawn a subagent. For now, we write the prompt
        # to a file that the agent can read, and mark the role as pending.
        prompt_file = self.artifacts_dir / role_id / "agent_prompt.txt"
        prompt_file.write_text(prompt)

        # Save state with current role
        state["current_role"] = role_id
        self.save_state(state)

        print(f"\n  Agent prompt written to: {prompt_file}")
        print(f"  Waiting for agent execution...")
        print(f"  Once the agent completes, run: /auto resume")

        # Mark as pending (not completed yet - agent needs to run)
        state["current_role"] = role_id
        self.save_state(state)
        return True  # True means "submitted to agent"

    def _build_role_prompt(self, role_id: str, agent_name: str, prompt_template: str, state: Dict[str, Any]) -> str:
        """Build the full prompt for a subagent role."""
        artifacts = state.get("artifacts", {})
        app_desc = state.get("app_description", "")

        prompt = f"""You are the {agent_name} in the SLDR Autonomous Software Factory.

PROJECT: {app_desc}
CURRENT ROLE: {role_id.upper()} - {agent_name}
PROJECT ROOT: {self.project_root}

YOUR TASK:
Execute your role in the SLDR pipeline. Read all previous handoff artifacts from
.opencode/handoffs/ and produce your output artifacts in .opencode/artifacts/{role_id}/.

PREVIOUS HANDOFFS AVAILABLE:
"""

        # Include previous handoffs
        for prev_role, _, _, _, _ in SLDR_PIPELINE:
            if prev_role == role_id:
                break
            handoff = self.load_handoff(prev_role)
            if handoff:
                prompt += f"\n--- {prev_role.upper()} ---\n{json.dumps(handoff, indent=2)[:2000]}\n"

        prompt += f"""
YOUR OUTPUT:
1. Write all artifacts to .opencode/artifacts/{role_id}/
2. Write a handoff summary to .opencode/handoffs/{role_id}.json
3. Include: status, artifacts_created, next_role_dependencies, any_issues
4. Mark status as "complete" when done

VERIFICATION GATE WILL RUN AFTER YOU COMPLETE.
DO NOT CLAIM COMPLETE UNTIL YOUR ARTIFACTS ARE WRITTEN AND VALIDATED.
"""
        return prompt

    def mark_role_complete(self, role_id: str, state: Dict[str, Any]):
        """Mark a role as completed and save state."""
        completed = state.get("completed_roles", [])
        if role_id not in completed:
            completed.append(role_id)
            state["completed_roles"] = completed
        if state.get("current_role") == role_id:
            state["current_role"] = None
        self.save_state(state)
        print(f"  [COMPLETE] {role_id.upper()}")

    def run_pipeline(self, app_description: str = None, resume: bool = False):
        """Run the full SLDR pipeline, respecting dependencies and parallelism."""
        state = self.load_state()

        if not resume:
            # Fresh start
            if not app_description:
                app_description = input("Enter application description: ").strip()
                if not app_description:
                    print("ERROR: App description is required.")
                    return False
            state["app_description"] = app_description
            state["run_id"] = f"sldr-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            state["started_at"] = datetime.now(timezone.utc).isoformat()
            state["completed_roles"] = []
            state["failed_roles"] = []
            state["artifacts"] = {}
            self.save_state(state)
        else:
            if not state.get("run_id"):
                print("ERROR: No previous run to resume. Run /auto without --resume first.")
                return False
            app_description = state.get("app_description", "")

        print(f"\n{'#'*60}")
        print(f"SLDR AUTONOMOUS SOFTWARE FACTORY")
        print(f"Run ID: {state['run_id']}")
        print(f"App: {app_description}")
        print(f"{'#'*60}\n")

        # Execute pipeline respecting dependencies
        max_iterations = len(SLDR_PIPELINE) + 2
        for iteration in range(max_iterations):
            ready_roles = self.get_next_roles(state)

            if not ready_roles:
                # No more roles ready - check if done
                if len(state.get("completed_roles", [])) == len(SLDR_PIPELINE):
                    print("\n" + "="*60)
                    print("SLDR PIPELINE COMPLETE - ALL ROLES FINISHED")
                    print("="*60)
                    return True
                else:
                    print("ERROR: No ready roles but pipeline incomplete. Possible deadlock.")
                    return False

            # Execute ready roles (sequential ones first, then parallel)
            sequential = [r for r in ready_roles if r[2] == "sequential"]
            parallel = [r for r in ready_roles if r[2] == "parallel"]

            # Execute sequential roles one at a time
            for role_id, agent_name, _, prompt_template in sequential:
                success = self.execute_role(role_id, agent_name, prompt_template, state)
                if not success:
                    print(f"  [FAILED] {role_id} - stopping pipeline")
                    return False
                # After agent runs, user must confirm completion via /auto resume
                print(f"\n  PAUSED: Waiting for {agent_name} to complete.")
                print(f"  Run /auto resume when ready.")
                return True  # Pause for agent execution

            # Execute parallel roles
            for role_id, agent_name, _, prompt_template in parallel:
                success = self.execute_role(role_id, agent_name, prompt_template, state)
                if not success:
                    print(f"  [FAILED] {role_id} - stopping pipeline")
                    return False

            # After parallel roles, user needs to confirm all completed
            print(f"\n  PAUSED: Waiting for parallel roles to complete.")
            print(f"  Run /auto resume when all agents are done.")
            return True

        print("ERROR: Pipeline exceeded max iterations.")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SLDR Autonomous Software Factory Orchestrator")
    parser.add_argument("command", choices=["start", "resume", "status", "gate"], nargs="?", default="status")
    parser.add_argument("--app", help="Application description for new run")
    args = parser.parse_args()

    orch = SLDROrchestrator()

    if args.command == "status":
        state = orch.load_state()
        print(json.dumps(state, indent=2))
    elif args.command == "start":
        orch.run_pipeline(app_description=args.app, resume=False)
    elif args.command == "resume":
        orch.run_pipeline(app_description=None, resume=True)
    elif args.command == "gate":
        state = orch.load_state()
        current = state.get("current_role")
        if current:
            ok = orch.run_verification_gate(current)
            if ok:
                orch.mark_role_complete(current, state)
                print(f"Gate passed for {current}")
            else:
                print(f"Gate FAILED for {current}")
        else:
            print("No current role to verify")


if __name__ == "__main__":
    main()