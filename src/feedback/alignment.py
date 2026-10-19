"""Align human and ASR transcripts and label ASR flags as false or genuine. Week 2-3.

An ASR flag is "genuine" if the human-transcript feedback has a flag of the same
category within one aligned word; otherwise it is "false" (ASR-induced).
Flags next to an insertion or deletion with no clear match are "ambiguous":
excluded from gate training and counted. About 100 labels are checked by hand
(docs/label_check.csv) and reported as label accuracy.
"""
from __future__ import annotations

from typing import Any


def align_words(human: dict[str, Any], asr: dict[str, Any]) -> list[tuple[int | None, int | None]]:
    """Return (human_index, asr_index) pairs from a word-level alignment (jiwer)."""
    raise NotImplementedError("TODO (C)")


def label_flags(human: dict[str, Any], asr: dict[str, Any]) -> dict[str, Any]:
    """Return the ASR record with `label` set on every feedback flag."""
    raise NotImplementedError("TODO (C)")
