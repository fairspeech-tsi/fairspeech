"""Grammar module (LanguageTool + spaCy). Week 1-2.

Input: a record with `transcript` and `words`.
Output: grammar flags appended to `record["feedback"]` (type "grammar").
"""
from src.text_normalise import normalise_token

# LanguageTool categories that describe grammar in speech; all others are ignored.
KEPT_LT_CATEGORIES = {"GRAMMAR", "CONFUSED_WORDS", "COLLOCATIONS", "NONSTANDARD_PHRASES", "MISC"}

# Rules inside the kept categories that fire on written-text conventions or on
# disfluencies (repetitions are speech, not grammar errors).
DISABLED_RULES = {
    "UPPERCASE_SENTENCE_START",
    "I_LOWERCASE",
    "MORFOLOGIK_RULE_EN_US",
    "WHITESPACE_RULE",
    "COMMA_PARENTHESIS_WHITESPACE",
    "EN_QUOTES",
    "PUNCTUATION_PARAGRAPH_END",
    "SENTENCE_WHITESPACE",
    "ENGLISH_WORD_REPEAT_RULE",
    "ENGLISH_WORD_REPEAT_BEGINNING_RULE",
    "EN_CONTRACTION_SPELLING",
}

def keep_match(rule_id: str, category: str) -> bool:
    """True if a LanguageTool match is a grammar issue we report for speech."""
    if rule_id in DISABLED_RULES:
        return False
    return category.upper() in KEPT_LT_CATEGORIES

def detect_grammar(record: dict, tool) -> tuple[list[dict], int]:
    """Return grammar flags for one record in the contract format, and the number
    of kept matches that could not be mapped to any word (see match_to_words).

    tool is anything with a check(text) method returning LanguageTool-style
    matches (rule_id, category, offset, error_length, message, replacements).
    """
    words = record["words"]
    text, spans = build_check_text(words)
    if not text:
        return [], 0

    by_index = {w["i"]: w for w in words}  # word index -> word object
    flags = []
    n_unmapped = 0

    for m in tool.check(text):
        if not keep_match(m.rule_id, m.category):
            continue

        hit = match_to_words(m.offset, m.error_length, spans)
        if not hit:
            n_unmapped += 1  # e.g. a zero-length match on a space
            continue

        # Take the full range of original words, including skipped fillers
        # inside it, so text and confidence describe what was actually said.
        ws, we = min(hit), max(hit)
        flagged = [by_index[i] for i in range(ws, we + 1)]
        confs = [w["confidence"] for w in flagged if w["confidence"] is not None]

        flags.append({
            "flag_id": "",  # numbered later, once all flag types are added
            "type": "grammar",
            "rule_id": m.rule_id,
            "category": group_category(m.rule_id, m.category, m.message),
            "word_start": ws,
            "word_end": we,
            "text": " ".join(w["word"] for w in flagged),
            "message": m.message,
            "suggestion": m.replacements[0] if m.replacements else None,
            "asr_confidence": min(confs) if confs else None,
            "label": None,  # filled by the alignment step
            "shown": True,  # every flag is shown before gating
        })

    return flags, n_unmapped

def number_flags(record: dict) -> None:
    """Sort all flags by position and give each the id <segment_id>:<source>:<n>.

    Covers every flag type, so it is rerun whenever a module adds flags.
    """
    type_order = {"grammar": 0, "filler": 1, "fluency": 2}  # tie-break on the same word
    record["feedback"].sort(
        key=lambda f: (f["word_start"], type_order.get(f["type"], 9), f["rule_id"])
    )
    for n, f in enumerate(record["feedback"]):
        f["flag_id"] = f"{record['segment_id']}:{record['source']}:{n}"


def add_grammar_feedback(record: dict, tool) -> int:
    """Replace the record's grammar flags with fresh ones and renumber all flags.

    Modifies record in place and keeps flags of other types, so it is safe to
    rerun. Returns the number of matches that could not be mapped to a word.
    """
    record["feedback"] = [f for f in record.get("feedback", []) if f["type"] != "grammar"]
    flags, n_unmapped = detect_grammar(record, tool)
    record["feedback"].extend(flags)
    number_flags(record)
    return n_unmapped

def build_check_text(words: list[dict]) -> tuple[str, list[tuple[int, int, int]]]:
    """Join normalised words with single spaces.
    Returns the text and a list of (char_start, char_end, word_index) spans,
    so a LanguageTool match can be mapped back to indices in record["words"].
    """
    parts = []   # normalised tokens that go into the checked text
    spans = []   # (char_start, char_end, word_index) for each token in parts
    pos = 0      # character position where the next token will start

    for w in words:
        tok = normalise_token(w["word"])
        if not tok:
            continue

        if parts:
            pos += 1 # the joining space added by " ".join

        spans.append((pos, pos + len(tok), w["i"]))
        parts.append(tok)
        pos += len(tok)

    return " ".join(parts), spans

def match_to_words(offset: int, length: int, spans: list[tuple[int, int, int]]) -> list[int]:
    """Return the word indices whose spans overlap the match [offset, offset + length).

    A match and a word overlap when the word starts before the match ends
    and ends after the match starts: s < m_end and e > m_start.
    """
    m_start = offset

    # Defensive: LanguageTool almost always marks at least one character, but a
    # rule that reports something missing could in theory return length 0. An
    # empty range overlaps no word, so the flag would be dropped silently.
    # Treating the length as at least 1 keeps such matches.
    # A zero-length match between two words (on the space) still overlaps
    # nothing and returns []. The caller skips and counts such matches
    # instead of guessing which word they belong to.

    # TODO: verify on the pilot data (count matches with length == 0) and update
    #       this comment with the result.

    m_end = max(m_start + length, m_start + 1)
    return [i for s, e, i in spans if s < m_end and e > m_start]

def group_category(rule_id: str, lt_category: str, message: str = "") -> str:
    """Map a LanguageTool rule to a project category (contract field `category`).

    LanguageTool has hundreds of rules and no grouping we can use directly, so
    rules are grouped by keywords in the rule ID and the message. Order matters:
    the first matching group wins. Anything unmatched is "other_grammar"; check
    the most frequent other_grammar rules on the pilot data and extend the map.
    """
    r = rule_id.upper()
    msg = message.lower()

    if ("AGR" in r or r in {"BASE_FORM", "NON3PRS_VERB", "DOES_X_HAS", "THIRD_PERSON_PLURAL", "SHE_LIVE"}
            or "agreement" in msg or "third-person" in msg or "third person" in msg):
        return "subject_verb_agreement"
    if "A_VS_AN" in r or r.startswith("EN_A_") or "ARTICLE" in r or r.startswith("DT_") or "A_NNS" in r:
        return "article"
    if any(k in r for k in ("TENSE", "PAST", "PARTICIPLE", "HAVE_PART", "VBZ", "VBG", "VB_", "MD_", "GERUND", "INFINITIVE")):
        return "verb_form"
    if "PREP" in r:
        return "preposition"
    if "PLURAL" in r or "NNS" in r or "NUMBER" in r:
        return "noun_number"
    if lt_category.upper() == "CONFUSED_WORDS":
        return "confused_words"
    return "other_grammar"