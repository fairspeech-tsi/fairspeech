"""Tests for the metrics module."""
import pytest

from src.feedback.metrics import (
    ambiguous_share,
    false_feedback_rate,
    ffr_bounds,
    ffr_by_group,
    flag_rows,
    genuine_flag_recall,
    group_gap,
    missed_real_error_rate,
)


def row(label, shown=True, group="A"):
    return {"group": group, "label": label, "shown": shown, "type": "grammar", "category": "x"}


def flag(label, shown=True, ftype="grammar"):
    return {"type": ftype, "category": "x", "label": label, "shown": shown}


def test_flag_rows_skips_unlabelled_and_other_types():
    records = [{"segment_id": "s1", "feedback": [
        flag("false"),
        flag(None),
        {"type": "fluency", "category": "x", "label": None, "shown": True},
    ]}]
    rows = flag_rows(records, {"s1": "Caribbean"})
    assert rows == [{"group": "Caribbean", "label": "false", "shown": True,
                     "type": "grammar", "category": "x"}]


def test_ffr_ignores_ambiguous_and_hidden_flags():
    rows = [row("false"), row("genuine"), row("ambiguous"), row("false", shown=False)]
    assert false_feedback_rate(rows) == 0.5


def test_ffr_is_none_when_nothing_is_shown():
    assert false_feedback_rate([]) is None
    assert false_feedback_rate([row("ambiguous"), row("false", shown=False)]) is None


def test_ffr_by_group_is_sorted_and_per_group():
    rows = [row("false", group="Native"), row("genuine", group="Caribbean"),
            row("false", group="Caribbean")]
    rates = ffr_by_group(rows)
    assert list(rates) == ["Caribbean", "Native"]
    assert rates == {"Caribbean": 0.5, "Native": 1.0}


def test_gap_ignores_missing_groups():
    assert group_gap({"A": 0.30, "B": 0.10, "C": None, "D": 0.25}) == pytest.approx(0.20)
    assert group_gap({"A": 0.5, "B": None}) is None


def test_recall_counts_hidden_genuine_flags():
    rows = [row("genuine"), row("genuine"), row("genuine", shown=False), row("false")]
    assert genuine_flag_recall(rows) == pytest.approx(2 / 3)
    assert missed_real_error_rate(rows) == pytest.approx(1 / 3)


def test_recall_is_one_before_gating_and_none_without_genuine():
    assert genuine_flag_recall([row("genuine"), row("false")]) == 1.0
    assert genuine_flag_recall([row("false")]) is None
    assert missed_real_error_rate([row("false")]) is None


def test_ambiguous_share_and_bounds():
    rows = [row("false"), row("false"), row("genuine"), row("genuine"), row("ambiguous")]
    assert ambiguous_share(rows) == pytest.approx(0.2)
    low, high = ffr_bounds(rows)
    assert (low, high) == (pytest.approx(0.4), pytest.approx(0.6))
    assert low <= false_feedback_rate(rows) <= high
    assert ffr_bounds([]) is None


def test_unexpected_label_raises():
    with pytest.raises(KeyError):
        false_feedback_rate([row("Genuine")])
        
def test_missing_segment_in_groups_raises():
    with pytest.raises(KeyError, match="s1"):
        flag_rows([{"segment_id": "s1", "feedback": [flag("false")]}], {})