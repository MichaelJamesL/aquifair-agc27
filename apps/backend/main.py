"""Vercel entrypoint: the app lives in src/neraca, which Vercel does not put on sys.path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from neraca.main import app  # noqa: E402

__all__ = ["app"]
