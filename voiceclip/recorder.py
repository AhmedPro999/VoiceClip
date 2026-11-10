"""Microphone recorder: start() on key down, stop() on key up -> float32 16 kHz mono."""
import threading

import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self.recording = False

    def _callback(self, indata, frames, time_info, status):
        if self.recording:
            self._chunks.append(indata[:, 0].copy())

    def start(self) -> bool:
        with self._lock:
            if self.recording:
                return False
            self._chunks = []
            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    blocksize=1024,
                    callback=self._callback,
                )
                self._stream.start()
            except Exception as exc:
                self._stream = None
                raise RuntimeError(f"Microphone error: {exc}") from exc
            self.recording = True
            return True

    def stop(self) -> np.ndarray:
        with self._lock:
            if not self.recording:
                return np.zeros(0, dtype=np.float32)
            self.recording = False
            try:
                if self._stream is not None:
                    self._stream.stop()
                    self._stream.close()
            finally:
                self._stream = None
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            audio = np.concatenate(self._chunks).astype(np.float32)
            self._chunks = []
            return audio

    @staticmethod
    def duration(audio: np.ndarray, sample_rate: int) -> float:
        return len(audio) / float(sample_rate)

    @staticmethod
    def normalize(audio: np.ndarray) -> np.ndarray:
        """Light peak normalisation so quiet mics still transcribe well."""
        if audio.size == 0:
            return audio
        peak = float(np.max(np.abs(audio)))
        if peak > 0 and peak < 0.3:
            audio = audio * (0.9 / peak)
        return np.clip(audio, -1.0, 1.0)
