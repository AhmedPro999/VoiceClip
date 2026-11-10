"""Push-to-talk hotkeys built on a pynput low-level keyboard hook.

Design notes:
  * press (start) and release (stop) of the same combo are both needed,
  * the letter is matched by *scan code* so it works while the Windows keyboard
    layout is Arabic (the "A" key then types "ش"),
  * the letter is swallowed so it is not typed into the focused window,
  * when Alt is part of the combo, a Ctrl tap is injected on release so Windows
    does not move focus to the menu bar when Alt is let go.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable

from pynput import keyboard as pk

from .log import log

# Set-1 (QWERTY position) scan codes - layout independent.
_SCAN = {
    "esc": 1, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
    "-": 12, "=": 13, "backspace": 14, "tab": 15,
    "q": 16, "w": 17, "e": 18, "r": 19, "t": 20, "y": 21, "u": 22, "i": 23, "o": 24, "p": 25,
    "[": 26, "]": 27, "enter": 28,
    "a": 30, "s": 31, "d": 32, "f": 33, "g": 34, "h": 35, "j": 36, "k": 37, "l": 38,
    ";": 39, "'": 40, "`": 41, "\\": 43,
    "z": 44, "x": 45, "c": 46, "v": 47, "b": 48, "n": 49, "m": 50, ",": 51, ".": 52, "/": 53,
    "space": 57, "capslock": 58,
    "f1": 59, "f2": 60, "f3": 61, "f4": 62, "f5": 63, "f6": 64, "f7": 65, "f8": 66, "f9": 67,
    "f10": 68, "f11": 87, "f12": 88,
}

# Virtual-key codes for modifiers (generic + left/right variants).
_MOD_VK = {
    0x12: "alt", 0xA4: "alt", 0xA5: "alt",
    0x11: "ctrl", 0xA2: "ctrl", 0xA3: "ctrl",
    0x10: "shift", 0xA0: "shift", 0xA1: "shift",
    0x5B: "win", 0x5C: "win",
}
_MOD_NAMES = {
    "alt": "alt", "altgr": "alt", "option": "alt",
    "ctrl": "ctrl", "control": "ctrl",
    "shift": "shift",
    "win": "win", "windows": "win", "cmd": "win", "super": "win",
}

_WM_KEYDOWN, _WM_KEYUP, _WM_SYSKEYDOWN, _WM_SYSKEYUP = 0x0100, 0x0101, 0x0104, 0x0105
_DOWN = (_WM_KEYDOWN, _WM_SYSKEYDOWN)
_UP = (_WM_KEYUP, _WM_SYSKEYUP)


@dataclass
class Combo:
    name: str
    modifiers: frozenset[str]
    key: str
    scan_code: int
    vk: int | None
    on_press: Callable[[], None]
    on_release: Callable[[], None]
    active: bool = False

    @classmethod
    def parse(cls, name: str, spec: str, on_press, on_release) -> "Combo":
        parts = [p.strip().lower() for p in spec.split("+") if p.strip()]
        mods: set[str] = set()
        key: str | None = None
        for p in parts:
            if p in _MOD_NAMES:
                mods.add(_MOD_NAMES[p])
            else:
                key = p
        if key is None:
            raise ValueError(f"Hotkey '{spec}' needs a non-modifier key, e.g. alt+a")
        if key not in _SCAN:
            raise ValueError(f"Hotkey key '{key}' is not supported (use a letter, digit, F-key, space...)")
        vk = ord(key.upper()) if len(key) == 1 and key.isalnum() else None
        return cls(name, frozenset(mods), key, _SCAN[key], vk, on_press, on_release)

    def matches(self, vk: int, scan: int) -> bool:
        return scan == self.scan_code or (self.vk is not None and vk == self.vk)


class PushToTalk:
    def __init__(self):
        self._combos: list[Combo] = []
        self._held: set[str] = set()
        self._listener: pk.Listener | None = None
        self._ctl = pk.Controller()
        self._lock = threading.Lock()

    def add(self, name: str, spec: str, on_press, on_release):
        self._combos.append(Combo.parse(name, spec, on_press, on_release))

    def start(self):
        if self._listener is None:
            self._listener = pk.Listener(win32_event_filter=self._filter, suppress=False)
            self._listener.daemon = True
            self._listener.start()
            self._listener.wait()
            log.info("hotkeys active: %s", ", ".join(f"{c.name}={'+'.join(sorted(c.modifiers))}+{c.key}" for c in self._combos))

    def stop(self):
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    # Called on the hook thread for every key message. Returning False keeps
    # pynput from dispatching on_press/on_release (we don't use them). Calling
    # suppress_event() stops the key from reaching the focused window.
    def _filter(self, msg, data):
        vk, scan = data.vkCode, data.scanCode
        is_down = msg in _DOWN
        is_up = msg in _UP
        if not (is_down or is_up):
            return False

        mod = _MOD_VK.get(vk)
        if mod:
            with self._lock:
                if is_down:
                    self._held.add(mod)
                else:
                    self._held.discard(mod)
                    for c in self._combos:
                        if c.active and mod in c.modifiers:
                            c.active = False
                            self._fire(c.on_release)
            return False

        for c in self._combos:
            if not c.matches(vk, scan):
                continue
            with self._lock:
                if is_down:
                    if c.active:
                        self._listener.suppress_event()  # auto-repeat
                    if self._held == c.modifiers:
                        c.active = True
                        log.info("hotkey %s pressed", c.name)
                        self._fire(c.on_press)
                        # Tap Ctrl now, while Alt is still down: Windows then knows Alt was
                        # not pressed "alone", so releasing it (in any order) never moves
                        # focus to the menu bar of the app the user is typing in.
                        if "alt" in c.modifiers:
                            self._fire(self._tap_ctrl)
                        self._listener.suppress_event()
                else:
                    if c.active:
                        c.active = False
                        log.info("hotkey %s released", c.name)
                        self._fire(c.on_release)
                        self._listener.suppress_event()
        return False

    def _tap_ctrl(self):
        try:
            self._ctl.press(pk.Key.ctrl)
            self._ctl.release(pk.Key.ctrl)
        except Exception:
            pass

    @staticmethod
    def _fire(fn):
        threading.Thread(target=fn, daemon=True).start()
