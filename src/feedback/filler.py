"""Filler module: flags hesitation fillers (um, uh) in a transcript record.

Owner: C. Flags use the shared feedback format (docs/data_contracts.md).

Design decisions:
1. Only hesitation fillers are flagged (um/uh families, including elongated
   spellings such as "umm" or "errm"; see src/text_normalise.py). "mm"/"hmm"
   are mostly backchannels ("mm hmm" = I'm listening) and "ah"/"eh" are
   interjections, so they are removed before grammar checking but not flagged.
2. "like" and "you know" are out of scope: telling filler from real use needs
   context, and wrong guesses would add noise to the labels.
3. One flag per filler, so the gate can judge each one with its own confidence.
"""
from __future__ import annotations

from src.feedback.grammar import number_flags
from src.text_normalise import hesitation_rule

FILLER_MESSAGE = "Filler word. A short silent pause sounds more confident."


def detect_fillers(record: dict) -> list[dict]:
    """Return one filler flag per hesitation filler, in the contract format."""
    flags = []
    for w in record["words"]:
        rule_id = hesitation_rule(w["word"])
        if rule_id is None:
            continue
        flags.append({
            "flag_id": "",  # numbered by number_flags
            "type": "filler",
            "rule_id": rule_id,
            "category": "filler",
            "word_start": w["i"],
            "word_end": w["i"],
            "text": w["word"],
            "message": FILLER_MESSAGE,
            "suggestion": None,
            "asr_confidence": w["confidence"],
            "label": None,  # filled by the alignment step
            "shown": True,  # every flag is shown before gating
        })
    return flags


def count_fillers(record: dict) -> int:
    """Number of hesitation fillers, for fluency["filler_count"]."""
    return sum(hesitation_rule(w["word"]) is not None for w in record["words"])


def add_filler_feedback(record: dict) -> None:
    """Replace the record's filler flags with fresh ones and renumber all flags.

    Modifies record in place and keeps flags of other types, so it is safe to
    rerun. Rerunning resets label and shown on filler flags and can change
    flag_ids, so rerun alignment and gating afterwards.
    """
    record["feedback"] = [f for f in record.get("feedback", []) if f["type"] != "filler"]
    record["feedback"].extend(detect_fillers(record))
    number_flags(record)