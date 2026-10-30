"""
fbm/plugins.py — plugin system.

Loads third-party extensions from the plugins/ directory. Each plugin is a
Python module with an optional `register()` function that receives the fbm
core object and can hook into actions, commands, and workflows.
"""
from __future__ import annotations
import importlib, os, sys
from pathlib import Path
from fbm import core as C

PLUGINS_DIR = Path("plugins")
LOADED: dict[str, object] = {}


def discover() -> list[str]:
    """Discover all plugin modules in plugins/. Returns list of names."""
    if not PLUGINS_DIR.exists():
        return []
    names = []
    for f in sorted(PLUGINS_DIR.iterdir()):
        if f.suffix == ".py" and not f.name.startswith("_"):
            names.append(f.stem)
    return names


def load(name: str) -> object | None:
    """Load plugin *name* from plugins/. Returns the module or None."""
    if name in LOADED:
        return LOADED[name]

    path = PLUGINS_DIR / f"{name}.py"
    if not path.exists():
        C.notify(f"plugins: {name} not found", "warn")
        return None

    try:
        spec = importlib.util.spec_from_file_location(f"plugins.{name}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        LOADED[name] = mod

        # Call register() if it exists
        if hasattr(mod, "register"):
            mod.register(C)

        C.notify(f"plugins: loaded {name}", "info")
        return mod
    except Exception as e:
        C.notify(f"plugins: failed to load {name}: {e}", "error")
        return None


def load_all() -> list[str]:
    """Load all discovered plugins. Returns list of loaded names."""
    loaded = []
    for name in discover():
        if load(name):
            loaded.append(name)
    return loaded


class PluginManager:
    """Plugin manager with discover() and load_all()."""

    def discover(self):
        """Discover and load all plugins. Returns list of loaded names."""
        return load_all()

    def load(self, name):
        """Load a single plugin by name."""
        return load(name)


_manager = PluginManager()


def get_manager():
    """Return the singleton PluginManager."""
    return _manager


def main():
    C.load_env()
    names = load_all()
    print(f"plugins: {len(names)} loaded: {names}")
    print("plugins ok")


if __name__ == "__main__":
    main()