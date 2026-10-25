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

"""Join normalised words with single spaces.
Returns the text and a list of (char_start, char_end, word_index) spans,
so a LanguageTool match can be mapped back to indices in record["words"].
"""
def build_check_text(words: list[dict]) -> tuple[str, list[tuple[int, int, int]]]:
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
