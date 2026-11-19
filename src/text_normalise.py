"""Shared text normalisation for grammar checking (C) and WER (B).

Lowercase, remove punctuation (keep apostrophes inside words), drop fillers and
non-speech tags, restore the pronoun "I". Both transcript sources go through
the same rules, so differences in transcription style cannot create flags.
"""

from __future__ import annotations
import re

_NON_SPEECH = re.compile(r"^[\[<(].*[\]>)]$")   # sounds like [laughter], <noise>
_PUNCT = re.compile(r"[^\w']+")                 # everything except letters, numbers and apostrophes
# Typographic apostrophes and backticks, written as a straight apostrophe.
_APOSTROPHES = re.compile(r"[\u2018\u2019\u201a\u201b\u2032`]")

# Hesitation fillers, allowing elongated spellings (umm, uhh, errm).
# These are removed before grammar checking and flagged by the filler module.
HESITATIONS = {
    "FILLER_UM": re.compile(r"^u+h*m+$"),           # um, umm, uhm
    "FILLER_UH": re.compile(r"^(?:u+h+|e+r+m*)$"),  # uh, uhh, er, erm
}

# Backchannels and interjections: removed before grammar checking, never flagged.
_OTHER_NON_WORDS = re.compile(r"^(?:h*m+|m+h+m+|a+h+|e+h+)$")  # mm, hmm, mhm, ah, eh


def hesitation_rule(word: str) -> str | None:
    """Return FILLER_UM / FILLER_UH if the word is a hesitation filler, else None.

    Casing and punctuation are ignored, so "Um,", "UMM" and "[UH]" all match.
    """
    t = _PUNCT.sub("", word.lower())
    for rule_id, pattern in HESITATIONS.items():
        if pattern.match(t):
            return rule_id
    return None


def is_filler(word: str) -> bool:
    """True for hesitations, backchannels and interjections (removed before grammar)."""
    t = _PUNCT.sub("", word.lower())
    return hesitation_rule(t) is not None or bool(_OTHER_NON_WORDS.match(t))

def clean_token(token: str) -> str:
    """Lowercase and strip punctuation (inner apostrophes kept).

    Returns "" for non-speech tags and pure punctuation. Fillers are kept.
    """
    t = token.strip()
    if not t or _NON_SPEECH.match(t):
        return ""
    t = _APOSTROPHES.sub("'", t.lower())
    # Punctuation inside a token becomes a space, so "twenty-five" -> "twenty five"
    # matches the human transcript's "TWENTY FIVE"; edge apostrophes are dropped.
    pieces = (p.strip("'") for p in _PUNCT.sub(" ", t).split())
    return " ".join(p for p in pieces if p)


def normalise_token(token: str) -> str:
    """Normalise one token for checking. Return "" if it should be skipped.

    A token may become several words ("twenty-five" -> "twenty five"); fillers
    are removed from each of them and the pronoun "I" is restored.
    """
    words = []
    for t in clean_token(token).split():
        if is_filler(t):
            continue
        if t == "i" or t.startswith("i'"):
            t = "I" + t[1:]
        words.append(t)
    return " ".join(words)

def normalise_text(text: str) -> str:
    """Normalise a whole transcript (e.g. for WER): normalised words joined by single spaces."""
    tokens = (normalise_token(w) for w in text.split())
    return " ".join(t for t in tokens if t)