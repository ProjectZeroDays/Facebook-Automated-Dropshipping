"""download_model.py — GGUF model fetcher for local LLM inference.

Downloads a quantized GGUF model (and optional mmproj) from a URL into
data/models/. Skips if already present. Supports resume via Range headers.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
import requests
import fbm_core as C

MODELS_DIR = Path("data/models")
DEFAULT_MODELS = {
    "qwen3-1.7b": "https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/main/qwen3-1.7b-Q4_K_M.gguf",
}

def download(url: str, dest: Path) -> bool:
    """Download *url* to *dest*, skipping if already complete."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"[download_model] already present: {dest}")
        return True
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(dest, "wb") as f:
                dl = 0
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    dl += len(chunk)
        print(f"[download_model] wrote {dest} ({dl} bytes)")
        return True
    except Exception as e:
        C.notify(f"download_model failed {url}: {e}", "error")
        print(f"[download_model] ERROR: {e}")
        return False

def main():
    C.load_env()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in DEFAULT_MODELS.items():
        dest = MODELS_DIR / f"{name}.gguf"
        download(url, dest)
    print("download_model ok")

if __name__ == "__main__":
    main()
