"""File logger: voiceclip.log next to app.py (keeps the last ~1 MB)."""
import logging
from logging.handlers import RotatingFileHandler

from .settings import ROOT

LOG_PATH = ROOT / "voiceclip.log"

log = logging.getLogger("voiceclip")
if not log.handlers:
    log.setLevel(logging.DEBUG)
    _h = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=1, encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(threadName)s: %(message)s"))
    log.addHandler(_h)
    _c = logging.StreamHandler()
    _c.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    log.addHandler(_c)
