"""Glue: record -> transcribe -> (translate) -> clipboard -> notify."""
from __future__ import annotations

import os
import threading
import time
from collections import deque

import numpy as np
import pyperclip

from . import notifier, overlay
from .log import log
from .recorder import Recorder
from .settings import settings
from .gemini import GeminiProcessor
from .transcriber import OfflineTranscriber, OnlineTranscriber
from .translator import OfflineTranslator, OnlineTranslator


def _label(target: str) -> str:
    return "إنجليزي" if target == "english" else "عربي"


def offline_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


class Pipeline:
    def __init__(self):
        self.sample_rate = int(settings.get("audio", "sample_rate", default=16000))
        self.recorder = Recorder(self.sample_rate)
        self.offline_stt = OfflineTranscriber()
        self.online_stt = OnlineTranscriber()
        self.offline_mt = OfflineTranslator()
        self.online_mt = OnlineTranslator()
        self.gemini = GeminiProcessor()
        self.last_text = ""
        self.last_arabic = ""
        self.history: deque[tuple[str, str]] = deque(maxlen=20)  # (label, text), newest first
        self.status = "starting"
        self.on_status = lambda s: None
        self._target = None  # "arabic" | "english" while a push is active

    # ---- lifecycle -------------------------------------------------------
    def preload(self):
        """Warm the offline models in the background so the first push is fast."""
        def _work():
            settings.load()
            if settings.get("mode") == "offline" and not offline_available():
                log.warning("offline mode in config but not installed; switching to online")
                settings.set("online", "mode")
            if settings.get("mode", default="online") != "offline":
                self._set_status("ready")
                if not (settings.get("online", "api_key") or os.environ.get("VOICECLIP_API_KEY")):
                    notifier.notify("VoiceClip", "محتاج API key: افتح الإعدادات من قائمة الأيقونة وحطه في online.api_key", force=True)
                else:
                    notifier.notify("VoiceClip", "جاهز (وضع أونلاين). Alt+A عربي، Alt+E إنجليزي")
                return
            self._set_status("loading")
            try:
                self.offline_stt.load()
                threading.Thread(target=self.offline_mt.load, daemon=True).start()
                self._set_status("ready")
                notifier.notify(
                    "VoiceClip",
                    f"جاهز ({self.offline_stt.device_used}). Alt+A عربي، Alt+E إنجليزي",
                )
            except Exception as exc:
                log.exception("model preload failed")
                self._set_status("error")
                notifier.beep_error()
                notifier.notify("VoiceClip - خطأ في تحميل الموديل", str(exc), force=True)

        threading.Thread(target=_work, daemon=True).start()

    def _set_status(self, s: str):
        self.status = s
        try:
            self.on_status(s)
        except Exception:
            pass

    # ---- push-to-talk callbacks -----------------------------------------
    def begin(self, target: str):
        log.info("begin(%s) recording=%s", target, self.recorder.recording)
        if self.recorder.recording:
            return
        try:
            self.recorder.start()
        except Exception as exc:
            log.exception("microphone start failed")
            notifier.beep_error()
            notifier.notify("VoiceClip - الميكروفون", str(exc), force=True)
            return
        self._target = target
        self._set_status(f"recording:{target}")
        notifier.beep_start()
        overlay.get().show("recording", "🎙 بيسجل · " + _label(target))

    def end(self):
        log.info("end() recording=%s", self.recorder.recording)
        if not self.recorder.recording:
            return
        audio = self.recorder.stop()
        target = self._target or "arabic"
        self._target = None
        log.info("captured %.2fs of audio", Recorder.duration(audio, self.sample_rate))
        threading.Thread(target=self._process, args=(audio, target), daemon=True).start()

    # ---- the work --------------------------------------------------------
    def _process(self, audio: np.ndarray, target: str):
        min_s = float(settings.get("audio", "min_seconds", default=0.4))
        if Recorder.duration(audio, self.sample_rate) < min_s:
            log.info("too short (<%.1fs), ignored", min_s)
            self._fail(target, "التسجيل قصير جداً، استمر ضاغط وإنت بتتكلم")
            return
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        silence = float(settings.get("audio", "silence_peak", default=0.01))
        if peak < silence:
            log.info("silence: peak=%.4f < %.3f, not sent", peak, silence)
            self._fail(target, f"مفيش صوت مسموع (الميك مكتوم أو بعيد؟) · مستوى {peak:.3f}")
            return
        log.info("audio peak=%.3f", peak)
        overlay.get().show("processing", "⏳ بيحوّل · " + _label(target))
        audio = Recorder.normalize(audio)
        settings.load()  # pick up edits to config.json (e.g. a newly pasted API key)
        mode = settings.get("mode", default="online")
        if mode == "offline" and not offline_available():
            log.warning("offline mode selected but faster-whisper is not installed; using online")
            notifier.notify("VoiceClip", "الوضع الأوفلاين مش متسطب (شغّل install_offline.bat). هستخدم الأونلاين.", force=True)
            mode = "online"
            settings.set("online", "mode")
        self._set_status("processing")
        t0 = time.time()
        try:
            provider = settings.get("online", "provider", default="gemini")
            log.info("processing target=%s mode=%s provider=%s", target, mode, provider)
            english = None
            if mode == "online" and provider == "gemini":
                # Gemini listens to the audio itself; one request does both jobs.
                if target == "english":
                    arabic, english = self.gemini.transcribe_and_translate(audio, self.sample_rate)
                else:
                    arabic = self.gemini.transcribe(audio, self.sample_rate)
            elif mode == "online":
                arabic = self.online_stt.transcribe(audio, self.sample_rate)
            else:
                arabic = self.offline_stt.transcribe(audio)

            log.info("result arabic=%r english=%r", arabic, english)
            if not arabic and not english:
                self._fail(target, "مسمعتش كلام واضح، جرب تاني وقرّب من الميك")
                return

            self.last_arabic = arabic
            if target == "english":
                text = english
                if not text and arabic:
                    log.info("english empty, translating the Arabic text separately")
                    text = self._translate(arabic, audio, mode, provider)
                if not text:
                    self._fail(target, "سمعت العربي بس الترجمة فشلت، جرب تاني")
                    return
                title = "English → copied"
            else:
                text = arabic
                title = "عربي ← تم النسخ"

            pyperclip.copy(text)
            self.last_text = text
            self.history.appendleft(("EN" if target == "english" else "AR", text))
            notifier.beep_done()
            secs = time.time() - t0
            log.info("copied to clipboard in %.1fs", secs)
            notifier.notify(f"{title} ({secs:.1f}s)", text)
            pasted = self._auto_paste()
            overlay.get().show("done", "✅ " + _label(target), "", 700)
            self._set_status("ready")
        except Exception as exc:
            log.exception("processing failed")
            overlay.get().show("error", "❌ " + str(exc)[:110], "", 3500)
            notifier.beep_error()
            notifier.notify("VoiceClip - خطأ", str(exc), force=True)
            self._set_status("ready")

    def _fail(self, target: str, reason: str):
        """Recording produced nothing usable: red bar, error beep, toast."""
        notifier.beep_error()
        notifier.notify("VoiceClip - فشل التسجيل", reason)
        overlay.get().show("error", "❌ فشل التسجيل · " + _label(target), reason, 2200)
        self._set_status("ready")

    def _auto_paste(self) -> bool:
        """If enabled, press Ctrl+V so the text lands where the cursor is."""
        if not settings.get("auto_paste", default=False):
            return False
        try:
            from pynput.keyboard import Controller, Key, KeyCode

            kb = Controller()
            v_key = KeyCode.from_vk(0x56)  # real "V" key; a unicode 'v' is not a Ctrl+V shortcut
            time.sleep(0.15)  # let the clipboard settle and the target window regain focus
            kb.press(Key.ctrl)
            kb.press(v_key)
            kb.release(v_key)
            kb.release(Key.ctrl)
            log.info("auto-pasted")
            return True
        except Exception:
            log.exception("auto paste failed")
            return False

    def _translate(self, arabic: str, audio: np.ndarray, mode: str, provider: str = "gemini") -> str:
        if mode == "online" and provider == "gemini":
            return self.gemini.translate_text(arabic)
        if mode == "online":
            return self.online_mt.translate(arabic)
        # offline: NLLB first, Whisper's own translate task as fallback
        text = self.offline_mt.translate(arabic)
        if text:
            return text
        return self.offline_stt.transcribe(audio, task="translate")
