"""Gate features per flag. Weeks 4-5.

One row per ASR flag: confidence of the flagged word and its +-2-word window (one
feature per model, never compared across models), agreement of Whisper,
CrisperWhisper and Vosk on the flagged word, rule category, word frequency (Zipf)
and length, pauses before and after, local speech rate, segment mean confidence.
CrisperWhisper gives no word confidence by default: use it only for agreement.
Accent label and speaker ID are NOT features.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def build_features(asr_records: dict[str, list[dict[str, Any]]]) -> pd.DataFrame:
    """Return one row per flag with the features above, plus flag_id and label."""
    raise NotImplementedError("TODO (B)")
