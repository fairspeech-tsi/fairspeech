"""Tests for the filler module."""
from src.feedback import io
from src.feedback.filler import add_filler_feedback, count_fillers, detect_fillers


def make_record(text, confidences=None):
    """A contract-valid record with one word per whitespace token."""
    tokens = text.split()
    confidences = confidences or [None] * len(tokens)
    return {
        "schema_version": "0.1", "segment_id": "s1", "source": "whisper", "model": None,
        "transcript": text,
        "words": [{"i": i, "word": w, "start": None, "end": None, "confidence": c}
                  for i, (w, c) in enumerate(zip(tokens, confidences))],
        "fluency": None, "feedback": [], "created_at": "2026-10-27T00:00:00Z",
    }


def test_one_flag_per_hesitation_with_its_confidence():
    rec = make_record("Um, I uh think so", confidences=[0.6, 0.9, 0.3, 0.9, 0.9])
    flags = detect_fillers(rec)
    assert [(f["rule_id"], f["word_start"], f["text"], f["asr_confidence"]) for f in flags] == [
        ("FILLER_UM", 0, "Um,", 0.6),
        ("FILLER_UH", 2, "uh", 0.3),
    ]


def test_backchannels_and_real_words_are_not_flagged():
    rec = make_record("mm hmm I like it umbrella")
    assert detect_fillers(rec) == []
    assert count_fillers(rec) == 0


def test_repeated_fillers_are_separate_flags():
    assert count_fillers(make_record("um um uh")) == 3


def test_rerun_replaces_filler_flags_keeps_others_and_validates():
    rec = make_record("um he go home")
    rec["feedback"].append({
        "flag_id": "", "type": "grammar", "rule_id": "HE_VERB_AGR",
        "category": "subject_verb_agreement", "word_start": 2, "word_end": 2,
        "text": "go", "message": "x", "suggestion": "goes",
        "asr_confidence": None, "label": None, "shown": True,
    })
    add_filler_feedback(rec)
    add_filler_feedback(rec)
    assert [(f["flag_id"], f["type"]) for f in rec["feedback"]] == [
        ("s1:whisper:0", "filler"),
        ("s1:whisper:1", "grammar"),
    ]
    assert io.validate(rec) == []