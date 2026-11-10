"""VoiceClip - push-to-talk Arabic dictation / Arabic->English translation to clipboard.

Alt+A (hold) : speak Arabic  -> Arabic text copied
Alt+E (hold) : speak Arabic  -> English text copied
Runs as a tray icon (Qt). Right-click it for options.
"""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (QAction, QActionGroup, QBrush, QColor, QIcon, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from voiceclip import notifier, overlay
from voiceclip.hotkeys import PushToTalk
from voiceclip.log import LOG_PATH, log
from voiceclip.pipeline import Pipeline, offline_available
from voiceclip.settings import CONFIG_PATH, settings

STATUS_LABEL = {
    "starting": "جاري التشغيل...",
    "loading": "جاري تحميل الموديل...",
    "ready": "جاهز",
    "recording:arabic": "🎙 بيسجل (عربي)",
    "recording:english": "🎙 بيسجل (إنجليزي)",
    "processing": "⏳ بيحوّل...",
    "error": "خطأ في التحميل",
}

ICON_COLORS = {
    "idle": ("#4da3ff", "#2b6fdb"),
    "loading": ("#9a9a9a", "#6e6e6e"),
    "recording": ("#ff6b6b", "#d63a3a"),
    "processing": ("#ffc947", "#e09a00"),
    "error": ("#8d6e63", "#5d4037"),
}


def make_icon(top: str, bottom: str) -> QIcon:
    """Rounded square with a vertical gradient and a white microphone glyph."""
    size = 64
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    grad = QLinearGradient(0, 0, 0, size)
    grad.setColorAt(0, QColor(top))
    grad.setColorAt(1, QColor(bottom))
    path = QPainterPath()
    path.addRoundedRect(QRectF(2, 2, size - 4, size - 4), 16, 16)
    p.fillPath(path, QBrush(grad))
    # microphone
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("white"))
    p.drawRoundedRect(QRectF(25, 13, 14, 24), 7, 7)
    pen = QPen(QColor("white"), 4, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(19, 20, 26, 26), 0, -180 * 16)
    p.drawLine(QPointF(32, 46), QPointF(32, 52))
    p.drawLine(QPointF(25, 52), QPointF(39, 52))
    p.end()
    return QIcon(pm)


class App(QObject):
    status_sig = Signal(str)

    def __init__(self):
        super().__init__()
        self.qapp = QApplication(sys.argv)
        self.qapp.setQuitOnLastWindowClosed(False)
        self.qapp.setLayoutDirection(Qt.RightToLeft)
        self.qapp.setApplicationName("VoiceClip")
        self.icons = {k: make_icon(*v) for k, v in ICON_COLORS.items()}

        overlay.init()
        self.pipeline = Pipeline()
        self.pipeline.on_status = self.status_sig.emit  # worker threads -> Qt thread
        self.status_sig.connect(self._on_status)
        self.ptt = PushToTalk()

        self.tray = QSystemTrayIcon(self.icons["loading"])
        self.tray.setToolTip("VoiceClip")
        self.menu = QMenu()
        self._build_menu()
        self.menu.aboutToShow.connect(self._refresh_menu)
        self.tray.setContextMenu(self.menu)
        self.tray.show()

    # ---- menu --------------------------------------------------------------
    def _build_menu(self):
        m = self.menu
        self.a_status = m.addAction("")
        self.a_status.setEnabled(False)
        self.a_keys = m.addAction("")
        self.a_keys.setEnabled(False)
        m.addSeparator()

        def toggle(label, key, default, on_change=None):
            a = QAction(label, m, checkable=True)
            a.setChecked(bool(settings.get(key, default=default)))

            def _t(checked):
                settings.set(bool(checked), key)
                if on_change:
                    on_change(bool(checked))

            a.toggled.connect(_t)
            m.addAction(a)
            return a

        self.a_overlay = toggle("شريط الحالة على الشاشة", "overlay", True, self._overlay_changed)
        self.a_paste = toggle("لصق تلقائي مكان المؤشر", "auto_paste", False, self._paste_changed)
        self.a_notif = toggle("إشعارات ويندوز", "notifications", True, self._notif_changed)
        self.a_sounds = toggle("الأصوات (بيب)", "sounds", True)
        m.addSeparator()

        mode_menu = m.addMenu("الوضع")
        group = QActionGroup(mode_menu)
        group.setExclusive(True)
        self.a_offline = QAction("أوفلاين (على الجهاز)", group, checkable=True)
        self.a_online = QAction("أونلاين (Gemini / API)", group, checkable=True)
        mode_menu.addAction(self.a_offline)
        mode_menu.addAction(self.a_online)
        self.a_offline.triggered.connect(lambda: self._set_mode("offline"))
        self.a_online.triggered.connect(lambda: self._set_mode("online"))
        m.addSeparator()

        self.a_copy_last = m.addAction("نسخ آخر نص تاني", self._copy_last)
        self.a_copy_ar = m.addAction("نسخ آخر نص عربي", self._copy_last_arabic)
        self.history_menu = m.addMenu("سجل النصوص (اضغط للنسخ)")
        m.addAction("فتح ملف الإعدادات", self._open_config)
        m.addAction("فتح ملف اللوج", lambda: os.startfile(str(LOG_PATH)))
        m.addSeparator()
        m.addAction("إغلاق", self._quit)

    def _refresh_menu(self):
        settings.load()
        self.a_status.setText(f"الحالة: {STATUS_LABEL.get(self.pipeline.status, self.pipeline.status)}")
        self.a_keys.setText(
            f"عربي: {settings.get('hotkeys', 'arabic')}   |   إنجليزي: {settings.get('hotkeys', 'english')}"
        )
        for a, key, d in ((self.a_overlay, "overlay", True), (self.a_paste, "auto_paste", False),
                          (self.a_notif, "notifications", True), (self.a_sounds, "sounds", True)):
            a.blockSignals(True)
            a.setChecked(bool(settings.get(key, default=d)))
            a.blockSignals(False)
        online = settings.get("mode") != "offline"
        self.a_online.setChecked(online)
        self.a_offline.setChecked(not online)
        self.a_copy_last.setEnabled(bool(self.pipeline.last_text))
        self.a_copy_ar.setEnabled(bool(self.pipeline.last_arabic))

        self.history_menu.clear()
        if not self.pipeline.history:
            a = self.history_menu.addAction("لا يوجد نصوص بعد")
            a.setEnabled(False)
        for label, text in list(self.pipeline.history):
            preview = text if len(text) <= 60 else text[:57] + "..."
            self.history_menu.addAction(f"[{label}] {preview}", self._make_copier(text))

    # ---- actions ---------------------------------------------------------------
    def _overlay_changed(self, on: bool):
        if on:
            overlay.get().show("info", "شريط الحالة شغال ✅", "", 1500)

    def _paste_changed(self, on: bool):
        overlay.get().show("info", "اللصق التلقائي " + ("شغال ✅" if on else "مقفول"), "", 1500)

    def _notif_changed(self, on: bool):
        if on:
            notifier.notify("VoiceClip", "الإشعارات شغالة ✅", force=True)

    def _set_mode(self, mode: str):
        if settings.get("mode") == mode:
            return
        if mode == "offline" and not offline_available():
            overlay.get().show("error", "الوضع الأوفلاين مش متسطب", "شغّل install_offline.bat الأول", 3000)
            self.a_online.setChecked(True)
            return
        settings.set(mode, "mode")
        if mode == "online" and not settings.get("online", "api_key"):
            overlay.get().show("error", "الوضع أونلاين محتاج API key في config.json", "", 3000)
        else:
            overlay.get().show("info", "الوضع دلوقتي: " + ("أونلاين" if mode == "online" else "أوفلاين"), "", 1500)
        if mode == "offline":
            self.pipeline.preload()

    def _make_copier(self, text: str):
        def _copy():
            import pyperclip
            pyperclip.copy(text)
            overlay.get().show("done", "✅ اتنسخ", "", 1200)
        return _copy

    def _copy_last(self):
        if self.pipeline.last_text:
            self._make_copier(self.pipeline.last_text)()

    def _copy_last_arabic(self):
        if self.pipeline.last_arabic:
            self._make_copier(self.pipeline.last_arabic)()

    def _open_config(self):
        try:
            os.startfile(str(CONFIG_PATH))
        except Exception:
            subprocess.Popen(["notepad", str(CONFIG_PATH)])

    def _quit(self):
        self.ptt.stop()
        self.tray.hide()
        self.qapp.quit()

    # ---- status -> icon --------------------------------------------------------
    def _on_status(self, status: str):
        if status.startswith("recording"):
            key = "recording"
        elif status == "processing":
            key = "processing"
        elif status in ("loading", "starting"):
            key = "loading"
        elif status == "error":
            key = "error"
        else:
            key = "idle"
        self.tray.setIcon(self.icons[key])
        self.tray.setToolTip(f"VoiceClip - {STATUS_LABEL.get(status, status)}")

    # ---- run -------------------------------------------------------------------
    def run(self):
        self.ptt.add("arabic", settings.get("hotkeys", "arabic", default="alt+a"),
                     on_press=lambda: self.pipeline.begin("arabic"),
                     on_release=self.pipeline.end)
        self.ptt.add("english", settings.get("hotkeys", "english", default="alt+e"),
                     on_press=lambda: self.pipeline.begin("english"),
                     on_release=self.pipeline.end)
        self.ptt.start()
        self.pipeline.preload()
        overlay.get().show("info", "VoiceClip جاهز · Alt+A عربي · Alt+E إنجليزي", "", 1800)
        log.info("tray icon starting (log: %s)", LOG_PATH)
        code = self.qapp.exec()
        log.info("app exited")
        return code


def main():
    # Single instance guard via a named mutex.
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _mutex = kernel32.CreateMutexW(None, False, "VoiceClip_SingleInstance")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        notifier.notify("VoiceClip", "البرنامج شغال أصلاً في الـ tray.", force=True)
        sys.exit(0)
    sys.exit(App().run())


if __name__ == "__main__":
    main()
