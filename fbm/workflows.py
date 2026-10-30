"""
fbm/workflows.py — workflow engine.

Composable pipelines with retries. Workflows are defined as a list of steps,
each calling a registered function. Supports retry with backoff on failure.
"""
from __future__ import annotations
from typing import Callable
from dataclasses import dataclass, field
from datetime import datetime
from fbm import core as C

WORKFLOW_REGISTRY: dict[str, "Workflow"] = {}


@dataclass
class Step:
    name: str
    fn: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    retries: int = 3
    backoff: float = 2.0


@dataclass
class Workflow:
    name: str
    steps: list[Step] = field(default_factory=list)

    def add(self, name: str, fn: Callable, *args, retries: int = 3, **kwargs):
        self.steps.append(Step(name, fn, args, kwargs, retries, 2.0))
        return self

    def run(self) -> dict:
        """Execute all steps. Returns results dict."""
        results = {}
        for step in self.steps:
            attempt = 0
            while attempt < step.retries:
                try:
                    result = step.fn(*step.args, **step.kwargs)
                    results[step.name] = {"status": "ok", "result": result}
                    break
                except Exception as e:
                    attempt += 1
                    if attempt >= step.retries:
                        results[step.name] = {"status": "fail", "error": str(e)}
                        C.notify(f"workflow step {step.name} failed after {step.retries} retries: {e}", "error")
                    else:
                        import time
                        time.sleep(step.backoff * attempt)
        return results


def register(name: str, wf: Workflow = None, *, steps: list = None):
    """Register *wf* under *name*. Supports decorator usage."""
    def _decorator(w):
        WORKFLOW_REGISTRY[name] = w
        return w
    if wf is not None:
        return _decorator(wf)
    return _decorator


def run_workflow(name: str) -> dict:
    """Run workflow *name*. Returns results dict."""
    if name not in WORKFLOW_REGISTRY:
        return {"error": f"unknown workflow: {name}"}
    return WORKFLOW_REGISTRY[name].run()


def list_workflows() -> dict:
    """Return all registered workflows with step names."""
    return {name: [s.name for s in wf.steps] for name, wf in WORKFLOW_REGISTRY.items()}


# --- Built-in workflows ---

from fbm import samples, reprice

register("sample_gate", Workflow("sample_gate")
    .add("order_samples", samples.order, dry=False)
    .add("score_suppliers", samples.score))

register("reprice_cycle", Workflow("reprice_cycle")
    .add("fetch_comps", reprice.run))


def main():
    C.load_env()
    for name, steps in list_workflows().items():
        print(f"  {name}: {' -> '.join(steps)}")
    print("workflows ok")


if __name__ == "__main__":
    main()