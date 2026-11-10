"""Windows toast notifications + short beeps."""
from __future__ import annotations

import threading
import winsound

from .settings import settings

APP_NAME = "VoiceClip"

try:
    from winotify import Notification, audio as _wn_audio
except Exception:  # pragma: no cover
    Notification = None
    _wn_audio = None


def _beep(freq: int, ms: int):
    if not settings.get("sounds", default=True):
        return
    threading.Thread(target=lambda: winsound.Beep(freq, ms), daemon=True).start()


def beep_start():
    _beep(880, 70)


def beep_done():
    _beep(1320, 90)


def beep_error():
    _beep(300, 250)


def notify(title: str, message: str, force: bool = False):
    """Show a toast. Respects the notifications toggle unless force=True."""
    if not force and not settings.get("notifications", default=True):
        return
    if Notification is None:
        return

    def _show():
        try:
            toast = Notification(
                app_id=APP_NAME,
                title=title,
                msg=(message or "")[:400],
                duration="short",
            )
            if _wn_audio is not None:
                toast.set_audio(_wn_audio.Silent, loop=False)
            toast.show()
        except Exception:
            pass

    threading.Thread(target=_show, daemon=True).start()
