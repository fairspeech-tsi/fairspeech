"""Grammar module (LanguageTool + spaCy). Week 1-2.

Input: a record with `transcript` and `words`.
Output: grammar flags appended to `record["feedback"]` (type "grammar").
"""
from src.text_normalise import normalise_token

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