"""whisper.py — local transcription fallback for voice messages.

Transcribes voice messages using a local Whisper model (via faster-whisper
or whisper.cpp). Falls back gracefully if no model/audio is available.
"""
from __future__ import annotations
import os
from pathlib import Path
import fbm_core as C

MODELS_DIR = Path("data/models")
DEFAULT_MODEL = "base"

def transcribe(path: str) -> str:
    """Transcribe audio at *path*. Returns text or empty string on failure."""
    if not os.path.exists(path):
        return ""
    try:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(DEFAULT_MODEL, device="cpu", compute_type="int8")
            segments, _ = model.transcribe(path)
            return " ".join(s.text for s in segments)
        except ImportError:
            pass
        try:
            import whisper
            model = whisper.load_model(DEFAULT_MODEL)
            result = model.transcribe(path)
            return result.get("text", "")
        except ImportError:
            pass
        C.notify("whisper: no whisper backend installed", "warn")
    except Exception as e:
        C.notify(f"whisper: transcribe failed: {e}", "error")
    return ""

def main():
    C.load_env()
    print("whisper ok")

if __name__ == "__main__":
    main()
