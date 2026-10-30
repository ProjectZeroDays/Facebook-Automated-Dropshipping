"""fbm — autonomous Facebook Marketplace dropshipping operations."""
__version__ = "0.2.0"

def __getattr__(name):
    import importlib
    return importlib.import_module(f"fbm.{name}")
