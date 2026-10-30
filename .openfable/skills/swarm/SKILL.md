---
name: swarm
description: >
  Parallel task orchestrator for independent workloads (test, payload, sweep, cve).
  Spawns sub-agents as processes for maximum throughput.
triggers:
  - swarm
  - parallel
  - batch
category: automation
enabled: true
metadata:
  agent: swarm_orchestrator.py
---

# Swarm Orchestrator

Parallel task executor for independent workloads.

## Capabilities

- **test**: Run pytest subsets in parallel
- **payload**: Generate exploit artifacts from modules
- **sweep**: Router/network sweep and fuzz
- **cve**: Single CVE verification
- **batch**: Execute task lists from JSON files

## Usage

```bash
# Single task
/swarm test --payload '{"test_path": "tests/test_payloads.py"}'
/swarm payload --payload '{"module": "exploits.cve_2019_2215_bad_binder", "out": "dist/out.bin"}'
/swarm sweep --payload '{"cidr": "192.168.1.0/24"}'
/swarm cve --payload '{"ip": "192.168.0.1", "cve": "CVE-2026-4534"}'

# Batch from file
/swarm batch --file tasks.json --workers 12

# Watch progress
/swarm --status
```

## Task JSON format (for batch)

```json
[
  {"kind": "test", "payload": {"test_path": "tests/test_payloads.py"}},
  {"kind": "payload", "payload": {"module": "exploits.cve_2019_2215_bad_binder", "out": "dist/binder.bin"}},
  {"kind": "sweep", "payload": {"cidr": "192.168.1.0/24"}},
  {"kind": "cve", "payload": {"ip": "192.168.0.1", "cve": "CVE-2026-4534"}}
]
```

## Worker Kinds

| Kind | Payload | Description |
|------|---------|-------------|
| test | `{test_path, kwargs?}` | Run pytest subset |
| payload | `{module, out}` | Generate exploit artifact |
| sweep | `{cidr?, ip?}` | Router sweep / fuzz |
| cve | `{ip, cve}` | Single CVE check |

## Output

Results stored in `.swarm/results.json` keyed by task ID.