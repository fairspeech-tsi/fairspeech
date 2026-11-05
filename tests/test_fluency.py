"""Tests for the fluency module."""
from src.feedback import io
from src.feedback.fluency import add_fluency, compute_fluency


def make_record(timed_words):
    """A contract-valid record from (word, start, end) tuples; None times = untimed."""
    return {
        "schema_version": "0.1", "segment_id": "s1", "source": "whisper", "model": None,
        "transcript": " ".join(w for w, _, _ in timed_words),
        "words": [{"i": i, "word": w, "start": s, "end": e, "confidence": None}
                  for i, (w, s, e) in enumerate(timed_words)],
        "fluency": None, "feedback": [], "created_at": "2026-11-05T00:00:00Z",
    }


def test_metrics_on_a_simple_segment():
    rec = make_record([("Um,", 0.0, 0.3), ("I", 0.5, 0.6), ("have", 0.6, 0.9),
                       ("led", 0.9, 1.2), ("projects", 2.0, 2.6)])
    # 4 real words over 2.6 s; one pause of 0.8 s (led -> projects); the 0.2 s gap is too short
    assert compute_fluency(rec) == {"wpm": 92.3, "n_pauses": 1, "mean_pause_s": 0.8, "filler_count": 1}


def test_no_pauses_gives_zero_mean():
    rec = make_record([("I", 0.0, 0.3), ("have", 0.4, 0.6), ("led", 0.7, 1.0)])
    assert compute_fluency(rec) == {"wpm": 180.0, "n_pauses": 0, "mean_pause_s": 0.0, "filler_count": 0}


def test_threshold_is_inclusive():
    rec = make_record([("yes", 0.0, 0.5), ("sure", 1.0, 1.5)])  # gap exactly 0.5 s
    assert compute_fluency(rec)["n_pauses"] == 1


def test_filler_breaks_a_silent_gap():
    # Without "um" the gap would be 0.8 s; with it, two gaps of 0.3 s
    rec = make_record([("I", 0.0, 0.3), ("um", 0.6, 0.8), ("think", 1.1, 1.4)])
    fluency = compute_fluency(rec)
    assert fluency["n_pauses"] == 0
    assert fluency["filler_count"] == 1


def test_untimed_or_too_short_records_get_none():
    assert compute_fluency(make_record([("I", None, None), ("have", None, None)])) is None
    assert compute_fluency(make_record([("yes", 0.0, 0.4)])) is None


def test_add_fluency_gives_a_schema_valid_record():
    rec = make_record([("I", 0.0, 0.3), ("have", 0.4, 0.6), ("led", 0.7, 1.0)])
    add_fluency(rec)
    assert io.validate(rec) == []