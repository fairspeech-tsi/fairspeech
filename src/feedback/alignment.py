"""Alignment module: labels ASR flags as false, genuine or ambiguous.

Owner: C. Compares an ASR record with the human record of the same segment
(docs/data_contracts.md) and writes `label` on the ASR record's grammar and
filler flags. These labels train B's gate and give the false feedback rate.

Steps:
1. Both transcripts become alignment tokens: lowercase, no punctuation, no
   non-speech tags. Unlike grammar and WER, fillers are KEPT (as "um" / "uh"),
   because filler flags need a counterpart on the human side.
2. JiWER aligns the token lists (equal, substitute, insert, delete).
3. Each ASR flag gets the first label whose rule applies:
   1. every flagged token is an ASR insertion (never said)   -> false
   2. the human record has a flag of the same type and
      category within one aligned token                      -> genuine
   3. an insertion or deletion touches the flag              -> ambiguous
   4. otherwise                                              -> false
   Genuine is checked before ambiguous because Whisper often drops fillers:
   every dropped "um" is a deletion, and real errors next to it must not be
   thrown out of training.
"""
from __future__ import annotations

from collections import Counter

import jiwer

from src.text_normalise import clean_token, hesitation_rule

LABELLED_TYPES = {"grammar", "filler"}
FILLER_TOKENS = {"FILLER_UM": "um", "FILLER_UH": "uh"}


def align_token(word: str) -> str:
    """Token used for alignment: fillers in one spelling, "" for tags and punctuation."""
    rule_id = hesitation_rule(word)
    if rule_id is not None:
        return FILLER_TOKENS[rule_id]
    return clean_token(word)


def to_tokens(words: list[dict]) -> tuple[list[str], list[int]]:
    """Alignment tokens and, for each token, the index of its word in `words`."""
    tokens, word_index = [], []
    for w in words:
        tok = align_token(w["word"])
        if tok:
            tokens.append(tok)
            word_index.append(w["i"])
    return tokens, word_index


def align(ref: list[str], hyp: list[str]) -> tuple[list[int | None], list[bool]]:
    """Align human (ref) and ASR (hyp) tokens.

    Returns:
        hyp_to_ref: for each ASR token, the position of its human token, or
            None if the ASR inserted it.
        deletion_before: for each position 0..len(hyp), True if human tokens
            were dropped just before that ASR token (or at the end).
    """
    hyp_to_ref: list[int | None] = [None] * len(hyp)
    deletion_before = [False] * (len(hyp) + 1)
    if not hyp or not ref:
        return hyp_to_ref, deletion_before  # with no human tokens, everything is an insertion

    out = jiwer.process_words(" ".join(ref), " ".join(hyp))
    for chunk in out.alignments[0]:
        if chunk.type in ("equal", "substitute"):
            for k in range(chunk.hyp_end_idx - chunk.hyp_start_idx):
                hyp_to_ref[chunk.hyp_start_idx + k] = chunk.ref_start_idx + k
        elif chunk.type == "delete":
            deletion_before[chunk.hyp_start_idx] = True
        # "insert": hyp_to_ref stays None
    return hyp_to_ref, deletion_before


def _token_span(flag: dict, word_index: list[int]) -> list[int]:
    """Token positions covered by a flag's word range."""
    return [p for p, i in enumerate(word_index) if flag["word_start"] <= i <= flag["word_end"]]


def label_flag(flag, asr_pos, hyp_to_ref, deletion_before, human_spans) -> str:
    """Apply the four rules to one ASR flag (asr_pos = its token positions)."""
    if not asr_pos:
        return "ambiguous"  # nothing to align (should not happen)

    ref_pos = [hyp_to_ref[p] for p in asr_pos if hyp_to_ref[p] is not None]

    # Rule 1: the speaker never said any of the flagged words.
    if not ref_pos:
        return "false"

    # Rule 2: same type and category on the human side, within one token.
    lo, hi = min(ref_pos) - 1, max(ref_pos) + 1
    for (ftype, category), (h_lo, h_hi) in human_spans:
        if ftype == flag["type"] and category == flag["category"] and h_lo <= hi and h_hi >= lo:
            return "genuine"

    # Rule 3: an insertion or deletion touches the flag.
    first, last = min(asr_pos), max(asr_pos)
    neighbours = [p for p in (first - 1, last + 1) if 0 <= p < len(hyp_to_ref)]
    if any(hyp_to_ref[p] is None for p in neighbours + asr_pos):
        return "ambiguous"
    if any(deletion_before[p] for p in range(first, last + 2)):
        return "ambiguous"

    # Rule 4
    return "false"


def label_flags(human: dict, asr: dict) -> Counter:
    """Write `label` on the ASR record's grammar and filler flags, in place.

    The human record is not changed. Returns the number of flags per label.
    """
    if human["segment_id"] != asr["segment_id"]:
        raise ValueError(f"different segments: {human['segment_id']} vs {asr['segment_id']}")

    ref, ref_index = to_tokens(human["words"])
    hyp, hyp_index = to_tokens(asr["words"])
    hyp_to_ref, deletion_before = align(ref, hyp)

    human_spans = []
    for f in human["feedback"]:
        pos = _token_span(f, ref_index)
        if f["type"] in LABELLED_TYPES and pos:
            human_spans.append(((f["type"], f["category"]), (min(pos), max(pos))))

    counts: Counter = Counter()
    for f in asr["feedback"]:
        if f["type"] not in LABELLED_TYPES:
            continue
        f["label"] = label_flag(f, _token_span(f, hyp_index), hyp_to_ref, deletion_before, human_spans)
        counts[f["label"]] += 1
    return counts