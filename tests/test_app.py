"""Smoke tests for the Streamlit app: every mock example renders without errors."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.app.data import list_examples

PRACTICE = Path(__file__).resolve().parents[1] / "src" / "app" / "app_pages" / "practice.py"


@pytest.mark.parametrize("label", list(list_examples()))
def test_practice_page_renders_every_example(label):
    at = AppTest.from_file(str(PRACTICE), default_timeout=30).run()
    at.selectbox[0].select(label).run()
    assert not at.exception
    assert at.subheader[0].value == "Transcript"