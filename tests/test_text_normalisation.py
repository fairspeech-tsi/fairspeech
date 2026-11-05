"""Tests for the shared text normalisation (used by grammar checking and WER)."""
from src.text_normalise import normalise_text, normalise_token


def test_normalise_token():
    assert normalise_token("Job.") == "job"
    assert normalise_token("i") == "I"
    assert normalise_token("i'm") == "I'm"
    assert normalise_token("don't,") == "don't"
    assert normalise_token("um") == ""
    assert normalise_token("[laughter]") == ""
    assert normalise_token("...") == ""


def test_human_and_asr_styles_normalise_to_the_same_text():
    """Punctuation, casing and fillers must not make the two sources differ."""
    human = "i have led three projects in my last job"
    asr = "Um, I have led three projects in my last job."
    assert normalise_text(human) == normalise_text(asr) == "I have led three projects in my last job"