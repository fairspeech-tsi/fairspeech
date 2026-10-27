"""Tests for the shared text normalisation (used by grammar checking and WER)."""
from src.text_normalise import normalise_text, normalise_token
from src.text_normalise import hesitation_rule, is_filler


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

def test_hesitation_spellings():
    for w in ("um", "Um,", "UMM", "ummm", "uhm", "[UM]"):
        assert hesitation_rule(w) == "FILLER_UM", w
    for w in ("uh", "uhh", "er", "Errm", "[UH]"):
        assert hesitation_rule(w) == "FILLER_UH", w


def test_backchannels_are_removed_but_not_hesitations():
    for w in ("mm", "Hmm.", "mhm", "ah", "eh"):
        assert hesitation_rule(w) is None, w
        assert is_filler(w), w


def test_real_words_are_not_fillers():
    for w in ("like", "umbrella", "her", "error", "hum", "ahead"):
        assert hesitation_rule(w) is None, w
        assert not is_filler(w), w
