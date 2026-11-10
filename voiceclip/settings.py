"""Load / save config.json living next to the project root."""
import json
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
MODELS_DIR = ROOT / "models"

_lock = threading.Lock()

DEFAULTS = {
    "hotkeys": {"arabic": "alt+a", "english": "alt+e"},
    "mode": "online",
    "notifications": True,
    "sounds": True,
    "overlay": True,
    "auto_paste": False,
    "offline": {
        "whisper_model": "large-v3-turbo",
        "device": "auto",
        "translation_model": "facebook/nllb-200-distilled-600M",
    },
    "online": {
        "provider": "gemini",
        "api_key": "",
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-3.5-flash",
            "fast_model": "gemini-3.5-flash-lite",
            "reasoning_effort": "low",
            "timeout_seconds": 40,
            "total_budget_seconds": 100,
            "fallback_models": ["gemini-3.8-flash"],
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "transcribe_model": "whisper-1",
            "translate_model": "gpt-4o-mini",
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "transcribe_model": "whisper-large-v3",
            "translate_model": "llama-3.3-70b-versatile",
        },
    },
    "audio": {"sample_rate": 16000, "min_seconds": 0.4, "silence_peak": 0.01},
}


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Settings:
    def __init__(self):
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        with _lock:
            if CONFIG_PATH.exists():
                try:
                    user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                    self.data = _merge(DEFAULTS, user)
                except Exception:
                    self.data = dict(DEFAULTS)
            else:
                self.data = dict(DEFAULTS)
                self._write()

    def _write(self):
        CONFIG_PATH.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def save(self):
        with _lock:
            self._write()

    def get(self, *keys, default=None):
        node = self.data
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def set(self, value, *keys):
        node = self.data
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value
        self.save()


settings = Settings()
