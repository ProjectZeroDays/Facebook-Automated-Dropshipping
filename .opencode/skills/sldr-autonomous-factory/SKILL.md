---
id: sldr-autonomous-factory
name: SLDR Autonomous Software Factory
description: Builds full-stack applications autonomously from requirements to production using a specialized SLDR (Software Development Life Cycle Roles) agent group with artifact-based handoffs, verification gates, and intelligent resume capability.
---

# SLDR Autonomous Software Factory

This skill turns OpenCode (and compatible coding agents) into an autonomous software factory that goes from requirements to production-deployed application without human intervention.

## Architecture: SLDR Agent Group

| Role | Agent | Responsibility |
|------|-------|---------------|
| Product Analyst | `pa-agent` | Requirements → PRD, user stories, tech stack |
| System Architect | `arch-agent` | Database schema, API contracts, directory structure, security model |
| Lead Developer | `lead-agent` | Task breakdown, agent assignments, coding standards |
| Frontend Developer | `fe-agent` | UI components, pages, state management |
| Backend Developer | `be-agent` | API routes, business logic, database models |
| DevOps / SRE | `devops-agent` | Docker, CI/CD, deployment configs, monitoring |
| QA Engineer | `qa-agent` | Unit tests, integration tests, E2E, security scans |
| Release Manager | `release-agent` | Production readiness gate, versioning, deployment |

## How It Works

1. **Artifact-based handoffs**: JSON files in `.opencode/handoffs/` instead of chat
2. **Sequential where dependent, parallel where independent**
3. **Verification gates**: build, test, lint, security between every handoff
4. **Intelligent resume**: `/auto` analyzes current state and picks up where left off
5. **User prompting**: Asks for missing info before proceeding

## Commands

| Command | Description |
|---------|-------------|
| `/auto <requirements>` | Start or resume autonomous full-stack build |
| `/auto status` | Check current production readiness status |
| `/auto resume` | Resume from last saved handoff state |
| `/sldr status` | Detailed SLDR pipeline status |

## Installation

- Global: `C:\Users\Project Zero\.opencode\skills\sldr-autonomous-factory\`
- Per-project: `<project>/.opencode/skills/sldr-autonomous-factory\`
- OpenFable global: `C:\Users\Project Zero\.openfable\skills\sldr-autonomous-factory\`
