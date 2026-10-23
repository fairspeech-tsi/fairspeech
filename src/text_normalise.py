#Shared text normalisation for grammar checking (C) and WER (B).
# Lowercase, remove punctuation (keep apostrophes inside words), drop fillers and
# non-speech tags, restore the pronoun "I".

from __future__ import annotations
from typing import Any
import re

_NON_SPEECH = re.compile(r"^[\[<(].*[\]>)]$")   # sounds like [laughter], <noise>
_PUNCT = re.compile(r"[^\w']+")                 # everything except letters, numbers and apostrophes

FILLERS = {"um", "umm", "uh", "uhm", "erm", "er", "hmm", "mm", "ah", "eh"}

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

def normalise_text(text: str) -> str:
    """Normalise a whole transcript (e.g. for WER): normalised words joined by single spaces."""
    tokens = (normalise_token(w) for w in text.split())
    return " ".join(t for t in tokens if t)