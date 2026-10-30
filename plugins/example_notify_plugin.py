"""example_notify_plugin.py — example plugin that sends notifications on events."""
from fbm.plugins import get_manager
import fbm_core as C

def on_order_created(order):
    C.notify(f"[notify plugin] New order: {order.get('title', 'unknown')}", "info")
    print(f"[notify plugin] Order alert: {order.get('title', 'unknown')}")

def register():
    m = get_manager()
    import fbm.tracking as Tracking
    # Hook into tracking ingest
    Tracking._notify_plugin = on_order_created
    print("[notify plugin] registered")

if __name__ == "__main__":
    register()
