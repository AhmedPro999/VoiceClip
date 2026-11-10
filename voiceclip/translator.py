"""Arabic -> English. Online via an LLM, offline via NLLB (with Whisper as fallback)."""
from __future__ import annotations

import os
import threading

from .settings import MODELS_DIR, settings

SYSTEM_PROMPT = (
    "You are a professional Arabic-to-English translator. The input is spoken "
    "Arabic (often Egyptian dialect) transcribed from a voice recording. "
    "Translate it into natural, fluent, idiomatic English that a native speaker "
    "would write. Preserve the meaning, tone and register; fix obvious "
    "transcription slips using context; do not translate word-for-word. "
    "Output ONLY the English translation, with no quotes, notes or explanations."
)


class OnlineTranslator:
    def __init__(self):
        self._lock = threading.Lock()

    def _client(self):
        provider = settings.get("online", "provider", default="groq")
        api_key = settings.get("online", "api_key", default="") or os.environ.get(
            "VOICECLIP_API_KEY", ""
        )
        if not api_key:
            raise RuntimeError("No API key configured for online mode.")
        from openai import OpenAI

        return (
            OpenAI(api_key=api_key, base_url=settings.get("online", provider, "base_url")),
            settings.get("online", provider, "translate_model"),
        )

    def translate(self, arabic: str) -> str:
        client, model = self._client()
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": arabic},
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        return text.strip('"').strip()


class OfflineTranslator:
    """NLLB-200 via transformers. Returns None from translate() if unavailable."""

    def __init__(self):
        self._pipe = None
        self._lock = threading.Lock()
        self.available: bool | None = None

    def load(self) -> bool:
        with self._lock:
            if self._pipe is not None:
                return True
            if self.available is False:
                return False
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

                name = settings.get(
                    "offline", "translation_model", default="facebook/nllb-200-distilled-600M"
                )
                cache = str(MODELS_DIR / "translation")
                tok = AutoTokenizer.from_pretrained(name, cache_dir=cache, src_lang="arb_Arab")
                mdl = AutoModelForSeq2SeqLM.from_pretrained(name, cache_dir=cache)
                device = 0 if torch.cuda.is_available() else -1
                if device == 0:
                    mdl = mdl.half()
                self._pipe = pipeline(
                    "translation",
                    model=mdl,
                    tokenizer=tok,
                    src_lang="arb_Arab",
                    tgt_lang="eng_Latn",
                    device=device,
                )
                self.available = True
                return True
            except Exception:
                self.available = False
                return False

    def translate(self, arabic: str) -> str | None:
        if not self.load():
            return None
        with self._lock:
            out = self._pipe(arabic, max_length=512, num_beams=4)
        text = out[0]["translation_text"].strip()
        return text or None
