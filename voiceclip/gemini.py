"""Gemini provider: the model listens to the audio directly (no separate STT step).

Uses Google's OpenAI-compatible endpoint, so the same `openai` client works.
One request returns the Arabic transcript, or the transcript plus a professional
English translation, as JSON.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time

import numpy as np

from .log import log
from .settings import settings
from .transcriber import audio_to_wav_bytes

TRANSCRIBE_PROMPT = (
    "You are an expert Arabic transcriber. The audio is a person speaking Arabic, "
    "usually Egyptian dialect. Transcribe exactly what is said in Arabic script, "
    "keeping the dialect as spoken, with sensible punctuation. Do not translate, "
    "do not add commentary. If the audio has no human speech (silence, noise, music, tones), "
    "return an empty string.\n"
    'Respond with JSON only: {"arabic": "<transcript>"}'
)

TRANSLATE_PROMPT = (
    "You are an expert Arabic transcriber and a professional Arabic-to-English translator. "
    "The audio is a person speaking Arabic, usually Egyptian dialect.\n"
    "1. Transcribe exactly what is said, in Arabic script, keeping the dialect.\n"
    "2. Translate it into natural, fluent, idiomatic English that a native speaker would "
    "write. Preserve meaning, tone and register; do not translate word-for-word.\n"
    "If the audio has no human speech (silence, noise, music, tones), return empty strings.\n"
    'Respond with JSON only: {"arabic": "<transcript>", "english": "<translation>"}'
)


def encode_audio(audio: np.ndarray, sample_rate: int) -> tuple[bytes, str]:
    """MP3 at 32 kbps when lameenc is available (8x smaller upload), else WAV."""
    try:
        import lameenc

        enc = lameenc.Encoder()
        enc.set_bit_rate(32)
        enc.set_in_sample_rate(sample_rate)
        enc.set_channels(1)
        enc.set_quality(5)
        pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
        return bytes(enc.encode(pcm)) + bytes(enc.flush()), "mp3"
    except Exception:
        return audio_to_wav_bytes(audio, sample_rate), "wav"


def _extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {}


class GeminiProcessor:
    def __init__(self):
        self._cached = None      # (key, base_url, timeout) -> OpenAI client
        self._cached_sig = None

    def _client(self):
        api_key = settings.get("online", "api_key", default="") or os.environ.get(
            "VOICECLIP_API_KEY", ""
        )
        if not api_key:
            raise RuntimeError(
                "No API key. Put your Gemini key in config.json -> online.api_key "
                "(get one free at aistudio.google.com)."
            )
        from openai import OpenAI

        g = lambda k, d=None: settings.get("online", "gemini", k, default=d)  # noqa: E731
        main = g("model", "gemini-3.5-flash")
        fast = g("fast_model", "") or main
        fallbacks = list(g("fallback_models", []) or [])

        def order(first: list[str]) -> list[str]:
            out: list[str] = []
            for m in first + fallbacks:
                if m and m not in out:
                    out.append(m)
            return out

        sig = (api_key, g("base_url"), float(g("timeout_seconds", 40)))
        if self._cached is None or self._cached_sig != sig:
            # Build once and reuse: keeps the TLS connection warm (saves seconds per request).
            self._cached = OpenAI(api_key=sig[0], base_url=sig[1], timeout=sig[2], max_retries=0)
            self._cached_sig = sig
        # Transcription only -> fastest model first; translation -> best model first.
        return self._cached, {"transcribe": order([fast, main]), "translate": order([main, fast])}

    def build_messages(self, audio: np.ndarray, sample_rate: int, translate: bool) -> list:
        data, fmt = encode_audio(audio, sample_rate)
        b64 = base64.b64encode(data).decode("ascii")
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": TRANSLATE_PROMPT if translate else TRANSCRIBE_PROMPT},
                    {"type": "input_audio", "input_audio": {"data": b64, "format": fmt}},
                ],
            }
        ]

    def _ask(self, audio: np.ndarray, sample_rate: int, translate: bool) -> dict:
        from openai import APIStatusError, APITimeoutError, APIConnectionError

        client, orders = self._client()
        models = orders["translate" if translate else "transcribe"]
        messages = self.build_messages(audio, sample_rate, translate)
        # "low" skips most of the model's internal thinking: ~3x faster, same transcript.
        effort = settings.get("online", "gemini", "reasoning_effort", default="low")
        extra = {"reasoning_effort": effort} if effort and effort != "default" else {}
        budget = float(settings.get("online", "gemini", "total_budget_seconds", default=100))
        started = time.time()
        last_err: Exception | None = None
        resp = None
        for model in models:
            if time.time() - started > budget:
                break
            t0 = time.time()
            try:
                resp = client.chat.completions.create(
                    model=model, temperature=0.2, messages=messages, **extra
                )
                log.info("gemini %s answered in %.1fs (%s)", model, time.time() - t0, messages[0]["content"][1]["input_audio"]["format"])
                break
            except APIStatusError as exc:
                last_err = exc
                log.warning("gemini %s failed in %.1fs: HTTP %s", model, time.time() - t0, exc.status_code)
                # 404 = model retired, 429 = quota, 5xx = overloaded: try the next model.
                if exc.status_code in (404, 429) or exc.status_code >= 500:
                    continue
                raise
            except (APITimeoutError, APIConnectionError) as exc:
                last_err = exc
                log.warning("gemini %s failed in %.1fs: %s", model, time.time() - t0, type(exc).__name__)
                continue
        if resp is None:
            status = getattr(last_err, "status_code", None)
            if status == 429:
                raise RuntimeError("خلصت حصة Gemini المجانية (في الدقيقة أو اليوم). استنى دقيقة وجرب تاني.")
            if status in (401, 403):
                raise RuntimeError("مفتاح Gemini غلط أو اتلغى. افتح الإعدادات وحط مفتاح صح.")
            if status == 404:
                raise RuntimeError("أسماء الموديلات في الإعدادات مش متاحة. غيّر model في config.json.")
            if status is None:
                raise RuntimeError("النت مش واصل لجوجل. اتأكد من الاتصال وجرب تاني.")
            raise RuntimeError(f"جوجل رجّع خطأ {status}. جرب تاني بعد شوية.")
        content = resp.choices[0].message.content or ""
        data = _extract_json(content)
        if not data and content.strip():
            # Model ignored the JSON instruction: treat the raw text as the answer.
            data = {"english" if translate else "arabic": content.strip()}
        return data

    def translate_text(self, arabic: str) -> str:
        """Text-only fallback when the audio request returned Arabic but no English."""
        client, orders = self._client()
        prompt = (
            "Translate this spoken Egyptian Arabic into natural, fluent English. "
            "Output ONLY the translation.\n\n" + arabic
        )
        for model in orders["translate"]:
            try:
                resp = client.chat.completions.create(
                    model=model, temperature=0.2, reasoning_effort="low",
                    messages=[{"role": "user", "content": prompt}],
                )
                text = (resp.choices[0].message.content or "").strip().strip('"')
                if text:
                    log.info("gemini %s translated text fallback", model)
                    return " ".join(text.split())
            except Exception as exc:
                log.warning("text translate on %s failed: %s", model, type(exc).__name__)
        return ""

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        return " ".join(str(self._ask(audio, sample_rate, False).get("arabic", "")).split())

    def transcribe_and_translate(self, audio: np.ndarray, sample_rate: int) -> tuple[str, str]:
        data = self._ask(audio, sample_rate, True)
        arabic = " ".join(str(data.get("arabic", "")).split())
        english = " ".join(str(data.get("english", "")).split())
        return arabic, english
