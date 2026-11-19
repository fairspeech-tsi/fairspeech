"""Shared data loading for the app pages.

Pages import from here instead of reading files themselves, so file locations
and validation live in one place.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.feedback import io

ROOT = Path(__file__).resolve().parents[2]
MOCK_DIR = ROOT / "data" / "mock"


def list_examples() -> dict[str, Path]:
    """Mock records the app can show, as {label: path}, sorted by label.

    Includes data/mock/feedback_example.json (label "feedback_example") and
    every JSON file in data/mock/grammar_examples/<source>/ (label like
    "mock_pair1 · whisper").
    """
    examples = {"feedback_example": MOCK_DIR / "feedback_example.json"}
    for source_dir in (MOCK_DIR / "grammar_examples").iterdir():
        if not source_dir.is_dir():
            continue
        for path in sorted(source_dir.glob("*.json")):
            label = f"{path.stem} · {source_dir.name}"
            examples[label] = path
    return dict(examples.items())


@st.cache_data
def load_record(path: Path) -> dict:
    """Load and validate one feedback record. Raises ValueError if invalid."""
    rec = io.load(path)
    errors = io.validate(rec)
    if errors:
        raise ValueError(f"Invalid record {path}: {errors}")
    return rec