"""Checks that the mock feedback JSON follows the shared contract."""
from pathlib import Path

from src.feedback import io

ROOT = Path(__file__).resolve().parents[1]


def test_mock_feedback_is_valid():
    record = io.load(ROOT / "data" / "mock" / "feedback_example.json")
    assert io.validate(record) == []


def test_flag_word_indices_exist():
    record = io.load(ROOT / "data" / "mock" / "feedback_example.json")
    n = len(record["words"])
    for flag in record["feedback"]:
        assert 0 <= flag["word_start"] <= flag["word_end"] < n
