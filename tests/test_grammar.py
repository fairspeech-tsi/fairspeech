"""Tests for the grammar module.

Unit tests use a fake LanguageTool, so they run without Java and test our code
rather than LanguageTool's rules. The integration test runs the real
LanguageTool only when RUN_LT=1 is set.
"""
import os
import shutil
from types import SimpleNamespace

import pytest

from src.feedback import io
from src.feedback.grammar import add_grammar_feedback, build_check_text, detect_grammar


class FakeTool:
    """Returns fixed matches and records every text it was asked to check."""

    def __init__(self, matches):
        self.matches = matches
        self.seen = []

    def check(self, text):
        self.seen.append(text)
        return self.matches


def match(rule_id, category, offset, length, replacements=(), message="Grammar error."):
    """A LanguageTool-style match with the attributes detect_grammar reads."""
    return SimpleNamespace(rule_id=rule_id, category=category, offset=offset,
                           error_length=length, message=message,
                           replacements=list(replacements))


def make_record(text, source="whisper", confidences=None):
    """A contract-valid record with one word per whitespace token."""
    tokens = text.split()
    confidences = confidences or [None] * len(tokens)
    return {
        "schema_version": "0.1",
        "segment_id": "s1",
        "source": source,
        "model": None,
        "transcript": text,
        "words": [{"i": i, "word": w, "start": None, "end": None, "confidence": c}
                  for i, (w, c) in enumerate(zip(tokens, confidences))],
        "fluency": None,
        "feedback": [],
        "created_at": "2026-10-26T00:00:00Z",
    }


def test_spans_keep_original_word_indices():
    rec = make_record("Um, I has led.")
    text, spans = build_check_text(rec["words"])
    assert text == "I has led"
    assert spans == [(0, 1, 1), (2, 5, 2), (6, 9, 3)]


def test_match_becomes_contract_flag():
    rec = make_record("um I has led three projects", confidences=[0.6, 0.98, 0.41, 0.9, 0.97, 0.93])
    tool = FakeTool([match("BASE_FORM", "GRAMMAR", 2, 3, ["have"], "Possible agreement error.")])
    add_grammar_feedback(rec, tool)

    assert tool.seen == ["I has led three projects"]
    (flag,) = rec["feedback"]
    assert (flag["word_start"], flag["word_end"], flag["text"]) == (2, 2, "has")
    assert flag["category"] == "subject_verb_agreement"
    assert flag["suggestion"] == "have"
    assert flag["asr_confidence"] == 0.41
    assert flag["flag_id"] == "s1:whisper:0"
    assert io.validate(rec) == []


def test_written_text_and_repeat_rules_are_dropped():
    rec = make_record("he go home")
    tool = FakeTool([
        match("UPPERCASE_SENTENCE_START", "CASING", 0, 2),
        match("MORFOLOGIK_RULE_EN_US", "TYPOS", 3, 2),
        match("ENGLISH_WORD_REPEAT_RULE", "MISC", 0, 2),
        match("HE_VERB_AGR", "GRAMMAR", 3, 2, ["goes"]),
    ])
    add_grammar_feedback(rec, tool)
    assert [f["rule_id"] for f in rec["feedback"]] == ["HE_VERB_AGR"]


def test_filler_inside_range_is_included_in_text_and_confidence():
    rec = make_record("I um has led", confidences=[0.98, 0.35, 0.88, 0.9])
    tool = FakeTool([match("BASE_FORM", "GRAMMAR", 0, 5)])  # "I has" in the checked text
    flags, _ = detect_grammar(rec, tool)
    assert flags[0]["text"] == "I um has"
    assert flags[0]["asr_confidence"] == 0.35


def test_human_transcript_has_no_confidence():
    rec = make_record("I has led", source="human")
    flags, _ = detect_grammar(rec, FakeTool([match("BASE_FORM", "GRAMMAR", 2, 3)]))
    assert flags[0]["asr_confidence"] is None


def test_zero_length_match_on_space_is_counted_not_flagged():
    rec = make_record("I has led")
    flags, n_unmapped = detect_grammar(rec, FakeTool([match("SOME_RULE", "GRAMMAR", 5, 0)]))
    assert flags == []
    assert n_unmapped == 1


def test_rerun_replaces_grammar_flags_and_keeps_others():
    rec = make_record("he go home")
    rec["feedback"].append({
        "flag_id": "", "type": "filler", "rule_id": "FILLER_UM", "category": "filler",
        "word_start": 0, "word_end": 0, "text": "he", "message": "x", "suggestion": None,
        "asr_confidence": None, "label": None, "shown": True,
    })
    tool = FakeTool([match("HE_VERB_AGR", "GRAMMAR", 3, 2, ["goes"])])
    add_grammar_feedback(rec, tool)
    add_grammar_feedback(rec, tool)
    assert sorted(f["type"] for f in rec["feedback"]) == ["filler", "grammar"]
    assert [f["flag_id"] for f in rec["feedback"]] == ["s1:whisper:0", "s1:whisper:1"]


def test_empty_transcript_does_not_call_the_tool():
    rec = make_record("um uh")
    tool = FakeTool([])
    assert detect_grammar(rec, tool) == ([], 0)
    assert tool.seen == []


@pytest.mark.skipif(os.environ.get("RUN_LT") != "1" or not shutil.which("java"),
                    reason="set RUN_LT=1 (needs Java 17+) to run the real LanguageTool")
def test_real_languagetool_flags_asr_error_but_not_human():
    import language_tool_python

    tool = language_tool_python.LanguageTool("en-US")
    try:
        human = make_record("I have led three projects in my last job", source="human")
        asr = make_record("I has led three projects in my last job.")
        add_grammar_feedback(human, tool)
        add_grammar_feedback(asr, tool)
    finally:
        tool.close()
    assert human["feedback"] == []
    assert any(f["text"] == "has" and f["category"] == "subject_verb_agreement"
               for f in asr["feedback"])