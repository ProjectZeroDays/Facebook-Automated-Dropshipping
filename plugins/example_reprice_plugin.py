"""example_reprice_plugin.py — example plugin that auto-reprices on schedule."""
from fbm.plugins import get_manager
import fbm.reprice as Reprice

def on_daily_pipeline(ctx):
    changed = Reprice.run()
    print(f"[reprice plugin] repriced {len(changed)} SKUs")
    ctx["reprice_changed"] = len(changed)
    return ctx

def register():
    m = get_manager()
    # The plugin manager's run_hook calls hooks by name
    # We register our function to be called on the "daily_pipeline" hook
    import fbm.workflows as Wf
    # Store reference so workflow can call it
    Wf._reprice_plugin = on_daily_pipeline
    print("[reprice plugin] registered")

if __name__ == "__main__":
    register()
