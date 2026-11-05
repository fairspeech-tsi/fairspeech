"""Fluency module: speaking rate and pauses from word timings.

Owner: C. Fills record["fluency"] (docs/data_contracts.md).

Design decisions:
1. Needs word timings, so only ASR records get fluency; human transcripts
   (no timings) keep fluency = None.
2. Metrics only, no flags: the gate works on grammar and filler flags
   (proposal), and the app shows these metrics as feedback.
3. Speaking time runs from the first word's start to the last word's end, so
   leading and trailing silence is ignored. WPM counts real words only (not
   fillers or tags), but filler time stays in the speaking time.
4. A pause is a silent gap of at least PAUSE_S between consecutive timed words.
   A filler breaks a gap ("I ... um ... think" is two short gaps, not one long
   one); filled pauses are counted by the filler module.
Whisper's word timings are approximate, so pause lengths are too.
"""
from __future__ import annotations

from src.feedback.filler import count_fillers
from src.text_normalise import normalise_token

PAUSE_S = 0.5  # minimum silent gap counted as a pause, in seconds


def compute_fluency(record: dict) -> dict | None:
    """Return the fluency metrics for one record, or None without word timings."""
    timed = [w for w in record["words"] if w["start"] is not None and w["end"] is not None]
    if len(timed) < 2:
        return None

    speaking_s = timed[-1]["end"] - timed[0]["start"]
    if speaking_s <= 0:
        return None

    n_words = sum(1 for w in record["words"] if normalise_token(w["word"]))
    pauses = [
        nxt["start"] - prev["end"]
        for prev, nxt in zip(timed, timed[1:])
        if nxt["start"] - prev["end"] >= PAUSE_S
    ]
    return {
        "wpm": round(60 * n_words / speaking_s, 1),
        "n_pauses": len(pauses),
        "mean_pause_s": round(sum(pauses) / len(pauses), 2) if pauses else 0.0,
        "filler_count": count_fillers(record),
    }


def add_fluency(record: dict) -> None:
    """Set record["fluency"] in place. Safe to rerun."""
    record["fluency"] = compute_fluency(record)