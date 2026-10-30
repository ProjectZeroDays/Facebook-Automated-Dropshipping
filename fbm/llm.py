"""llm.py — local llama.cpp sidecar, with API-key and stub fallbacks."""
from __future__ import annotations
import json, os, shutil, subprocess, time
from pathlib import Path
import requests

MODELS_DIR = Path(os.getenv("FBM_MODELS", "data/models"))
PORT = int(os.getenv("FBM_LLM_PORT", "8081"))
BASE = f"http://127.0.0.1:{PORT}"

# tier by device RAM; all Apache-2.0-clean or permissive for commercial use
TIERS = [(4, "gemma-3-1b-it-Q4_K_M.gguf"), (6, "Qwen3-1.7B-Q4_K_M.gguf"),
         (99, "Llama-3.2-3B-Instruct-Q4_K_M.gguf")]

LOCKED = ("You are the assistant inside an app that runs a Facebook Marketplace shop. "
          "Answer ONLY from CONTEXT. If it isn't in CONTEXT, say so briefly. "
          "Never invent prices or delivery dates. Be warm, human and short (max 3 sentences).")

def pick_model():
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    except Exception:
        ram = 8.0
    for limit, name in TIERS:
        if ram <= limit:
            return MODELS_DIR / name
    return MODELS_DIR / TIERS[-1][1]

def local_up():
    try:
        return requests.get(f"{BASE}/health", timeout=1.5).ok
    except Exception:
        return False

def start_local():
    if local_up(): return True
    model = pick_model()
    if not model.exists(): return False
    exe = shutil.which("llama-server")
    if exe:
        cmd = [exe, "-m", str(model), "--port", str(PORT), "--host", "127.0.0.1",
               "-t", str(os.cpu_count() or 4), "--ctx-size", "4096", "--n-predict", "256"]
    else:  # fallback to the python server if llama.cpp isn't installed
        cmd = [os.sys.executable, "-m", "llama_cpp.server", "--model", str(model),
               "--port", str(PORT), "--n_ctx", "4096"]
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return False
    for _ in range(20):
        if local_up(): return True
        time.sleep(1)
    return False

def backend():
    if local_up(): return "local"
    if os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"): return "api"
    return "stub"

def ask(prompt, context="", task="chat"):
    b = backend()
    if b == "local":
        try:
            r = requests.post(f"{BASE}/v1/chat/completions", timeout=120, json={
                "messages": [{"role": "system", "content": f"{LOCKED}\nTASK: {task}"},
                             {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{prompt}"}],
                "temperature": 0.4, "max_tokens": 256})
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
    if b == "api":
        try:
            key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
            url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            r = requests.post(f"{url}/chat/completions", timeout=60,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": os.getenv("LLM_MODEL", "gpt-4o-mini"), "temperature": 0.4,
                      "messages": [{"role": "system", "content": LOCKED},
                                   {"role": "user", "content": f"CONTEXT:\n{context}\n\n{prompt}"}]})
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
    return _stub(prompt, context)

def _stub(prompt, context):
    p = prompt.lower()
    if "explain" in p or "this screen" in p:
        return ("This screen shows your shop's key numbers and the actions you can take. "
                "Use the tabs to move between products, orders and settings.")
    if any(k in p for k in ("price", "margin", "profit")):
        return "Your margins live on the products screen - aim for 35%+ after fees."
    if any(k in p for k in ("order", "ship")):
        return "Orders needing action are flagged red. Ship within 3 business days."
    if any(k in p for k in ("hello", "hi", "hey")):
        return "Hi! Ask me anything about your shop, a product, or the app."
    return f"(stub) You asked: {prompt[:120]}. Install a model or set OPENAI_API_KEY for real answers."
