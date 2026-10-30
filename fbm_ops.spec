# ============================================================================
# PyInstaller spec for FBM Ops standalone .exe
# Build: pyinstaller fbm_ops.spec
# ============================================================================
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys

# --- Application entry point ---
entry = "app.py"

# --- Hidden imports (modules imported dynamically) ---
hiddenimports = [
    "fbm.core",
    "fbm.autovars",
    "fbm.bugreport",
    "fbm.reprice",
    "fbm.samples",
    "fbm.tracking",
    "fbm.watcher",
    "fbm.crosslist_post",
    "fbm.scraper",
    "fbm.targets",
    "fbm.bootstrap",
    "fbm.firstrun",
    "fbm.dashboard",
    "fbm.billing",
    "fbm.observability",
    "fbm.auth_hardening",
    "fbm.plugins",
    "fbm.commands",
    "fbm.workflows",
    "fbm.agents",
    "fbm.actions",
    "fbm.payments",
    "fbm.drip",
    "fbm.onboarding_emails",
    "fbm.emailcopy",
    "fbm.adminroutes",
    "fbm.tenants",
    "fbm.selfheal",
    "fbm.insights",
    "fbm.inbox",
    "fbm.inbox_poller",
    "fbm.google",
    "fbm.download_model",
    "fbm.updater",
    "fbm.whisper",
    "fbm.metrics",
    "fbm.profile_backup",
    "fbm.inbox_ai",
    "fbm.daemon",
    "fbm.setup",
    "fbm.default_commands",
    "fbm.web_pages",
    "fbm.security",
    "fbm.mcp_client",
    "fbm.mcp_integration",
    "fbm.chatbot",
    "fbm.llm",
    "fbm.webhooks",
    "fbm.accounts",
    "fbm.suppliers",
    "fbm.groups",
    "fbm.crosslist",
    "fbm.returns",
    "fbm.tax",
    "fbm.deadman",
    "fbm.fbm_validate",
    "fbm.targets_builder",
    "fbm.copy_generator",
    "fbm.session_guard",
    "playwright.sync_api",
    "playwright._impl",
    "flask",
    "gunicorn",
    "requests",
    "pillow",
    "pyotp",
    "prometheus_client",
]

# --- Data files (templates, static, selectors, etc.) ---
datas = [
    ("fbm/templates", "fbm/templates"),
    ("fbm/static", "fbm/static"),
    ("selectors.json", "."),
    ("fbm_state.json", "."),
    (".env.example", "."),
    ("requirements.txt", "."),
    ("suppliers.json", "."),
    ("inventory.csv", "."),
    ("skus.csv", "."),
    ("groups.txt", "."),
    ("policy.md", "."),
]

# Add Playwright browser binaries (critical for browser automation)
try:
    from playwright._impl._browser import chromium
    pw_browser = Path(chromium.executable_path).parent.parent
    if pw_browser.exists():
        datas.append((str(pw_browser), "playwright/.local-browsers"))
except Exception:
    pass

a = Analysis(
    [entry],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="fbm-ops",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Optionally: icon="assets/icon.ico"
)

app = BUNDLE(
    exe,
    name="fbm-ops.app",
    bundle_identifier=None,
)