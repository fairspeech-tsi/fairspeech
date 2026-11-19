"""Tests for the alignment module."""
from pathlib import Path

import pytest

from src.feedback import io
from src.feedback.alignment import align, align_token, label_flags

EXAMPLES = Path("data/mock/grammar_examples")
SVA = "subject_verb_agreement"


def rec(source, text, flags, segment_id="s1"):
    """A minimal record: one word per token, flags as (type, category, start, end)."""
    words = [{"i": i, "word": w, "start": None, "end": None, "confidence": None}
             for i, w in enumerate(text.split())]
    feedback = [{"type": t, "category": c, "word_start": a, "word_end": b, "label": None}
                for t, c, a, b in flags]
    return {"segment_id": segment_id, "source": source, "words": words, "feedback": feedback}


def label_of(human_text, asr_text, human_flags, asr_flags):
    asr = rec("whisper", asr_text, asr_flags)
    label_flags(rec("human", human_text, human_flags), asr)
    return asr["feedback"][0]["label"]


def test_align_tokens_keep_fillers_in_one_spelling():
    assert [align_token(w) for w in ["Um,", "UMM", "[UH]", "Erm", "Have.", "<LAUGH>"]] == [
        "um", "um", "uh", "uh", "have", ""]


def test_align_marks_insertions_and_deletions():
    hyp_to_ref, deletion_before = align(["the", "people", "was", "angry"],
                                        ["the", "people", "is", "was", "angry"])
    assert hyp_to_ref == [0, 1, None, 2, 3]
    hyp_to_ref, deletion_before = align(["he", "has", "gone", "home"], ["he", "gone", "home"])
    assert hyp_to_ref == [0, 2, 3]
    assert deletion_before == [False, True, False, False]


@pytest.mark.parametrize("human, asr, human_flags, asr_flags, expected", [
    # rule 4: substitution, no human flag
    ("I have led", "I has led", [], [("grammar", SVA, 1, 1)], "false"),
    # rule 2: same flag on the human side
    ("he don't like it", "He don't like it.", [("grammar", SVA, 1, 1)], [("grammar", SVA, 1, 1)], "genuine"),
    # rule 2 before rule 3: Whisper dropped "um" next to a real error
    ("she don't um like it", "She don't like it.", [("grammar", SVA, 1, 1)], [("grammar", SVA, 1, 1)], "genuine"),
    # rule 3: deletion next to the flag
    ("he has gone home", "he gone home", [], [("grammar", "verb_form", 1, 1)], "ambiguous"),
    # rule 1: invented filler
    ("I think", "um I think", [], [("filler", "filler", 0, 0)], "false"),
    # rule 1 before rule 2: inserted word next to a real human error
    ("the people was angry", "the people is was angry", [("grammar", SVA, 2, 2)], [("grammar", SVA, 2, 2)], "false"),
    # categories match, rule_ids may differ: human "uh", Whisper "um"
    ("uh I think", "Um, I think.", [("filler", "filler", 0, 0)], [("filler", "filler", 0, 0)], "genuine"),
    # different category on the human side does not count
    ("he don't like it", "He don't like it.", [("grammar", "article", 1, 1)], [("grammar", SVA, 1, 1)], "false"),
])
def test_labelling_rules(human, asr, human_flags, asr_flags, expected):
    assert label_of(human, asr, human_flags, asr_flags) == expected


def test_counts_and_human_record_unchanged():
    human = rec("human", "I have led", [])
    asr = rec("whisper", "um I has led", [("filler", "filler", 0, 0), ("grammar", SVA, 2, 2)])
    assert label_flags(human, asr) == {"false": 2}
    assert human["feedback"] == []


def test_different_segments_raise():
    with pytest.raises(ValueError):
        label_flags(rec("human", "hi", [], "s1"), rec("whisper", "hi", [], "s2"))


@pytest.mark.parametrize("segment_id, expected", [
    ("mock_pair1", ["false"]),
    ("mock_pair2", ["false"]),
    ("mock_pair3", ["false"]),
    ("mock_pair4", ["genuine"]),
    ("mock_pair5", []),
])
def test_grammar_examples_get_expected_labels(segment_id, expected):
    """End to end: real LanguageTool flags from the example pairs (README table)."""
    human = io.load(EXAMPLES / "human" / f"{segment_id}.json")
    asr = io.load(EXAMPLES / "whisper" / f"{segment_id}.json")
    label_flags(human, asr)
    assert [f["label"] for f in asr["feedback"]] == expected
    assert io.validate(asr) == []