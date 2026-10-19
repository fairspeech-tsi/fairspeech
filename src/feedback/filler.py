"""Filler module: um, uh, erm, filler 'like' and 'you know'. Week 2-3."""
from __future__ import annotations

from typing import Any

FILLERS = {"um", "umm", "uh", "uhm", "erm", "er", "hmm"}


def detect_fillers(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return filler flags (type "filler") for one transcript."""
    raise NotImplementedError("TODO (C)")
