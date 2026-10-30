import sys, pathlib, os, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import pytest

@pytest.fixture
def env(monkeypatch, tmp_path):
    db = tmp_path / "test.db"
    monkeypatch.setenv("FBM_DB", str(db))
    monkeypatch.setenv("FBM_PROFILE", str(tmp_path / "prof"))
    # import after env set
    import importlib
    import fbm.core as core
    importlib.reload(core)
    core.init_db()
    # expose as module-like object
    class Env:
        pass
    e = Env()
    e.db = core.db
    e.core = core
    e.tmp_path = tmp_path
    # register env in sys.modules? tests use env.db()
    return e

# import compat shims
try:
    import fbm._compat
except Exception:
    pass
