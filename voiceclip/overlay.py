"""Modern status capsule (Qt): rounded, soft shadow, fade in/out, pulsing dot while
recording. Never takes keyboard focus. Thread-safe: show()/hide() may be called
from any thread; they are queued onto the Qt main thread through a signal.

States: recording (red, pulsing), processing (amber), done (green),
error (red), info (blue).
"""
from __future__ import annotations

from PySide6.QtCore import (QEasingCurve, QObject, QPropertyAnimation, Qt, QTimer,
                            QVariantAnimation, Signal)
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout,
                               QWidget)

from .settings import settings

COLORS = {
    "recording": "#ff5252",
    "processing": "#ffb300",
    "done": "#4cd964",
    "error": "#ff5252",
    "info": "#4da3ff",
}
PILL_BG = QColor(28, 28, 30, 242)      # #1c1c1e, slightly translucent
PILL_BORDER = QColor(255, 255, 255, 28)
FG = "#f5f5f7"
FG_DIM = "#a1a1a6"
RADIUS = 13
SHADOW_MARGIN = 14


class _Dot(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(8, 8)
        self.color = QColor(COLORS["info"])
        self.level = 1.0

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(self.color)
        c.setAlphaF(self.level)
        p.setPen(Qt.NoPen)
        p.setBrush(c)
        p.drawEllipse(self.rect())


class _Card(QWidget):
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(0, 0, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(r, RADIUS, RADIUS)
        p.fillPath(path, PILL_BG)
        p.setPen(QPen(PILL_BORDER, 1))
        p.drawPath(path)


class _Pill(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setLayoutDirection(Qt.RightToLeft)

        self._card = _Card(self)
        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 140))
        self._card.setGraphicsEffect(shadow)

        self._dot = _Dot()
        self._title = QLabel()
        self._title.setFont(QFont("Segoe UI Variable Text", 9, QFont.DemiBold))
        self._title.setStyleSheet(f"color: {FG}; background: transparent;")
        self._detail = QLabel()
        self._detail.setFont(QFont("Segoe UI Variable Text", 8))
        self._detail.setStyleSheet(f"color: {FG_DIM}; background: transparent;")
        self._detail.setWordWrap(True)
        self._detail.setMaximumWidth(420)

        texts = QVBoxLayout()
        texts.setContentsMargins(0, 0, 0, 0)
        texts.setSpacing(1)
        texts.addWidget(self._title)
        texts.addWidget(self._detail)

        row = QHBoxLayout(self._card)
        row.setContentsMargins(12, 5, 11, 5)
        row.setSpacing(8)
        row.addWidget(self._dot, 0, Qt.AlignVCenter)
        row.addLayout(texts)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN)
        outer.addWidget(self._card)

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.finished.connect(self._after_fade)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.fade_out)

        self._pulse = QVariantAnimation(self)
        self._pulse.setStartValue(1.0)
        self._pulse.setEndValue(0.25)
        self._pulse.setDuration(650)
        self._pulse.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse.setLoopCount(-1)
        self._pulse.valueChanged.connect(self._on_pulse)
        self._pulse_dir = 1

    def _on_pulse(self, v):
        # ping-pong: loop goes 1 -> .25 repeatedly, mirror every other loop for a smooth pulse
        if self._pulse.currentLoop() % 2 == 1:
            v = 1.25 - v
        self._dot.level = float(v)
        self._dot.update()

    def present(self, state: str, title: str, detail: str, hide_after_ms):
        self._hide_timer.stop()
        self._fade.stop()
        self._dot.color = QColor(COLORS.get(state, COLORS["info"]))
        self._dot.level = 1.0
        self._dot.update()
        self._title.setText(title)
        self._detail.setText(detail)
        self._detail.setVisible(bool(detail))
        if state == "recording":
            if self._pulse.state() != QVariantAnimation.Running:
                self._pulse.start()
        else:
            self._pulse.stop()

        self.adjustSize()
        geo = QGuiApplication.primaryScreen().availableGeometry()
        w, h = self.width(), self.height()
        self.move(geo.x() + (geo.width() - w) // 2, geo.y() + geo.height() - h - 20)

        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
            self._fade.setDuration(100)
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.start()
        else:
            self.setWindowOpacity(1.0)
        if hide_after_ms:
            self._hide_timer.start(int(hide_after_ms))

    def fade_out(self):
        if not self.isVisible():
            return
        self._pulse.stop()
        self._fade.stop()
        self._fade.setDuration(110)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def _after_fade(self):
        # Called after every fade; only a fade-out ends at zero opacity.
        if self.windowOpacity() <= 0.01:
            self.hide()


class Overlay(QObject):
    """Thread-safe facade. Must be constructed on the Qt main thread (after QApplication)."""

    _show_sig = Signal(str, str, str, object)
    _hide_sig = Signal()

    def __init__(self):
        super().__init__()
        self._pill = _Pill()
        self._show_sig.connect(self._pill.present)
        self._hide_sig.connect(self._pill.fade_out)

    def show(self, state: str, title: str, detail: str = "", hide_after_ms: int | None = None):
        if not settings.get("overlay", default=True):
            return
        self._show_sig.emit(state, title, detail, hide_after_ms)

    def hide(self):
        self._hide_sig.emit()


class _Null:
    def show(self, *a, **k):  # before the Qt app exists: drop silently
        pass

    def hide(self):
        pass


_instance: Overlay | _Null = _Null()


def init() -> Overlay:
    """Call once from the Qt main thread after QApplication is created."""
    global _instance
    if not isinstance(_instance, Overlay):
        _instance = Overlay()
    return _instance


def get():
    return _instance
