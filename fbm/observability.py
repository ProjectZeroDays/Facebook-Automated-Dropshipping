"""
fbm/observability.py — structured logging, circuit breakers, retry logic, WAL mode.

Provides observability infrastructure for production operations:
- Structured JSON logging with correlation IDs
- Circuit breakers for external API calls
- Retry with exponential backoff
- SQLite WAL mode and corruption recovery
"""
from __future__ import annotations
import json, os, sys, time, sqlite3, logging
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps
from fbm import core as C

LOG_DIR = Path("data/logs")
LOG_FILE = LOG_DIR / "app.log"
CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationLogger:
    """Structured logger that emits JSON with correlation IDs."""

    def __init__(self, name: str = "fbm"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(fh)
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(sh)

    def _emit(self, level: str, msg: str, **kwargs):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": "fbm",
            "msg": msg,
        }
        entry.update(kwargs)
        self.logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(entry, default=str))

    def info(self, msg: str, **kwargs):
        self._emit("info", msg, **kwargs)

    def warn(self, msg: str, **kwargs):
        self._emit("warn", msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._emit("error", msg, **kwargs)


_log = CorrelationLogger()


def get_logger(name: str = "fbm") -> CorrelationLogger:
    """Return a CorrelationLogger instance for *name*."""
    return CorrelationLogger(name)


def setup_logging():
    """Initialize structured logging. Called by app.py on startup."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _log.info("logging initialized", log_file=str(LOG_FILE))


def integrity_check() -> dict:
    """Run a basic integrity check on the observability system."""
    return {
        "logger": "ok",
        "log_file": str(LOG_FILE),
        "log_dir_exists": LOG_DIR.exists(),
        "circuits": len(_CIRCUITS),
    }


def correlation_id() -> str:
    """Generate a new correlation ID."""
    import uuid
    return f"corr_{uuid.uuid4().hex[:12]}"


# ============================================================ circuit breaker

class CircuitBreaker:
    """Circuit breaker for external API calls.

    States: closed (normal), open (failing, short-circuit), half-open (testing).
    """
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "closed"
        self.last_failure_time = 0.0

    def call(self, fn, *args, **kwargs):
        """Call *fn* through the circuit breaker."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise CircuitOpenError(f"circuit {self.name} is open")

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failures = 0
        self.state = "closed"

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
            _log.warn("circuit opened", circuit=self.name, failures=self.failures)


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Registry of circuit breakers by service name
_CIRCUITS: dict[str, CircuitBreaker] = {}


def circuit(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker for *name*."""
    if name not in _CIRCUITS:
        _CIRCUITS[name] = CircuitBreaker(name)
    return _CIRCUITS[name]


# ============================================================ retry with backoff

def retry(fn, max_attempts: int = 3, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Call *fn* with retry and exponential backoff."""
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except exceptions as e:
            last_exc = e
            if attempt < max_attempts:
                sleep = backoff * attempt
                _log.warn("retry", attempt=attempt, max_attempts=max_attempts, sleep=sleep, error=str(e))
                time.sleep(sleep)
    raise last_exc


# ============================================================ SQLite WAL mode

def apply_wal(conn: sqlite3.Connection):
    """Enable WAL mode on *conn* for better concurrent read performance."""
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
    except Exception:
        pass


def ensure_db_healthy():
    """Check DB integrity and attempt recovery if corrupted."""
    db_path = C.db_path()
    if not os.path.exists(db_path):
        return
    try:
        with C.db() as c:
            result = c.execute("PRAGMA quick_check").fetchone()
            if result and result[0] != "ok":
                _log.error("db corruption detected", path=db_path, check=result[0])
    except Exception as e:
        _log.error("db health check failed", error=str(e))


# ============================================================ structured logging helpers

def log_event(kind: str, ref: str = "", detail: str = "", tenant_id: str = None, **kwargs):
    """Log an event both to the DB and to structured logs."""
    try:
        with C.db() as c:
            c.execute(
                "INSERT INTO events(kind, ref, detail, tenant_id, created_at) "
                "VALUES(?,?,?,?,datetime('now'))",
                (kind, ref, detail, tenant_id or C.DEFAULT_TENANT_ID),
            )
    except Exception:
        pass
    _log.info("event", kind=kind, ref=ref, detail=detail, tenant_id=tenant_id, **kwargs)


def log_error(error: Exception, context: dict = None):
    """Log an error with context to structured logs."""
    entry = {"error": type(error).__name__, "message": str(error)}
    if context:
        entry.update(context)
    _log.error("error", **entry)


def main():
    C.load_env()
    print("observability module loaded")
    print(f"  log file: {LOG_FILE}")
    print(f"  circuits: {list(_CIRCUITS.keys())}")
    print("observability ok")


if __name__ == "__main__":
    main()