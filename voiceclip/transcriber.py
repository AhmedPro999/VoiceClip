"""Speech -> Arabic text. Offline (faster-whisper) or online (OpenAI-compatible API)."""
from __future__ import annotations

import io
import os
import sys
import threading
import wave
from pathlib import Path

import numpy as np

from .settings import MODELS_DIR, settings

# Prompt that nudges Whisper towards Modern/Egyptian Arabic with punctuation.
ARABIC_PROMPT = "السلام عليكم، إزيك عامل إيه؟ النهارده هنتكلم عن الشغل والمشروع الجديد."


def _add_nvidia_dll_dirs():
    """Make the pip-installed cuBLAS / cuDNN DLLs visible to CTranslate2."""
    if sys.platform != "win32":
        return
    try:
        import nvidia  # type: ignore
    except Exception:
        return
    for base in getattr(nvidia, "__path__", []):
        for sub in ("cublas", "cudnn", "cuda_runtime"):
            d = Path(base) / sub / "bin"
            if d.is_dir():
                try:
                    os.add_dll_directory(str(d))
                except Exception:
                    pass
                os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")


def audio_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


class OfflineTranscriber:
    def __init__(self):
        self._model = None
        self._lock = threading.Lock()
        self.device_used = None

    def load(self):
        with self._lock:
            if self._model is not None:
                return
            _add_nvidia_dll_dirs()
            from faster_whisper import WhisperModel

            name = settings.get("offline", "whisper_model", default="large-v3-turbo")
            device = settings.get("offline", "device", default="auto")
            MODELS_DIR.mkdir(exist_ok=True)

            attempts = []
            if device in ("auto", "cuda"):
                attempts.append(("cuda", "float16"))
                attempts.append(("cuda", "int8_float16"))
            if device in ("auto", "cpu"):
                attempts.append(("cpu", "int8"))

            last_err = None
            for dev, ctype in attempts:
                try:
                    self._model = WhisperModel(
                        name,
                        device=dev,
                        compute_type=ctype,
                        download_root=str(MODELS_DIR),
                    )
                    # Force CUDA init now so a broken GPU setup fails here, not mid-use.
                    self._model.transcribe(np.zeros(16000, dtype=np.float32), language="ar")
                    self.device_used = f"{dev}/{ctype}"
                    return
                except Exception as exc:  # try the next backend
                    last_err = exc
                    self._model = None
            raise RuntimeError(f"Could not load Whisper model '{name}': {last_err}")

    def transcribe(self, audio: np.ndarray, task: str = "transcribe") -> str:
        self.load()
        with self._lock:
            segments, _info = self._model.transcribe(
                audio,
                language="ar",
                task=task,
                beam_size=5,
                best_of=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 400},
                condition_on_previous_text=False,
                initial_prompt=ARABIC_PROMPT if task == "transcribe" else None,
            )
            text = " ".join(seg.text.strip() for seg in segments)
        return " ".join(text.split())


class OnlineTranscriber:
    def __init__(self):
        self._client = None
        self._lock = threading.Lock()

    def _get_client(self):
        with self._lock:
            provider = settings.get("online", "provider", default="groq")
            api_key = settings.get("online", "api_key", default="") or os.environ.get(
                "VOICECLIP_API_KEY", ""
            )
            if not api_key:
                raise RuntimeError(
                    "No API key. Put it in config.json -> online.api_key "
                    "or set the VOICECLIP_API_KEY environment variable."
                )
            from openai import OpenAI

            base_url = settings.get("online", provider, "base_url")
            self._client = OpenAI(api_key=api_key, base_url=base_url)
            self._model = settings.get("online", provider, "transcribe_model")
            return self._client

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        client = self._get_client()
        wav = audio_to_wav_bytes(audio, sample_rate)
        result = client.audio.transcriptions.create(
            model=self._model,
            file=("audio.wav", wav, "audio/wav"),
            language="ar",
            prompt=ARABIC_PROMPT,
            response_format="json",
            temperature=0.0,
        )
        text = getattr(result, "text", "") or ""
        return " ".join(text.split())
