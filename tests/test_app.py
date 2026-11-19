"""Smoke tests for the Streamlit app."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.app.data import list_examples
from src.app.notice import CONSENT_LABEL, FEEDBACK_DISCLAIMER, NOTICE_TITLE

PAGES = Path(__file__).resolve().parents[1] / "src" / "app" / "app_pages"


def practice():
    return AppTest.from_file(str(PAGES / "practice.py"), default_timeout=30).run()


@pytest.mark.parametrize("label", list(list_examples()))
def test_practice_page_renders_every_example(label):
    at = practice()
    at.selectbox[0].select(label).run()
    assert not at.exception
    assert any(FEEDBACK_DISCLAIMER in c.value for c in at.caption)


def test_record_and_upload_hidden_until_consent():
    at = practice()
    assert at.checkbox[0].label == CONSENT_LABEL
    assert not at.checkbox[0].value
    info = [i.value for i in at.info]
    assert any("Tick the box" in v for v in info)
    assert not any("Recording and upload" in v for v in info)

    at.checkbox[0].check().run()
    info = [i.value for i in at.info]
    assert any("Recording and upload" in v for v in info)
    assert not any("Tick the box" in v for v in info)


def test_about_page_shows_the_notice():
    at = AppTest.from_file(str(PAGES / "about.py"), default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value == NOTICE_TITLE