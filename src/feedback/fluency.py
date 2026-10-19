"""Fluency module: words per minute and pauses from word timestamps. Week 2-3."""
from __future__ import annotations

from typing import Any

PAUSE_THRESHOLD_S = 0.5


def compute_fluency(record: dict[str, Any]) -> dict[str, Any]:
    """Return the `fluency` object (wpm, n_pauses, mean_pause_s, filler_count)."""
    raise NotImplementedError("TODO (C)")
