"""Grammar module (LanguageTool + spaCy). Week 1-2.

Input: a record with `transcript` and `words`.
Output: grammar flags appended to `record["feedback"]` (type "grammar").
"""
from __future__ import annotations
from typing import Any
import re
from src.feedback.filler import FILLERS

_NON_SPEECH = re.compile(r"^[\[<(].*[\]>)]$")   # sounds like [laughter], <noise>
_PUNCT = re.compile(r"[^\w']+")                 # everything except letters, numbers and apostrophes


def normalise_token(token: str) -> str:
    """Normalize a token for checking. Return "" if it should be skipped."""
    t = token.strip()
    if not t or _NON_SPEECH.match(t):
        return ""
    
    t = _PUNCT.sub("", t.lower()).strip("'")

    if not t or t in FILLERS:
        return ""

    if t == "i" or t.startswith("i'"):
     t = "I" + t[1:]
    return t


def detect_grammar(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return grammar flags for one transcript, mapped to word indices."""
    raise NotImplementedError("TODO (C): LanguageTool check + map character offsets to word indices")
