"""Tests for the app's audio pipeline, with a fake ASR and a fake LanguageTool."""
from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest

from src.app import pipeline
from src.app.pipeline import analyse, decode, to_record
from src.feedback import io


@pytest.fixture
def fake_decode(monkeypatch):
    """Replace audio decoding with silence of a chosen length (no audio files needed)."""
    def use(seconds):
        monkeypatch.setattr(pipeline, "decode", lambda audio: np.zeros(int(seconds * pipeline.SAMPLE_RATE)))
    return use


class FakeASR:
    """Returns a fixed Whisper-style result and records what it received."""

    def __init__(self, words):
        self.words = words
        self.calls = []

    def transcribe(self, audio, **kwargs):
        self.calls.append((audio, kwargs))
        words = [{"i": i, "word": w, "start": 0.5 * i, "end": 0.5 * i + 0.4, "confidence": c}
                 for i, (w, c) in enumerate(self.words)]
        return {"source": "whisper", "model": "faster-whisper-base",
                "transcript": " ".join(w for w, _ in self.words), "words": words}


class FakeTool:
    def check(self, text):
        if text.startswith("I has"):
            return [SimpleNamespace(rule_id="BASE_FORM", category="GRAMMAR", offset=2, error_length=3,
                                    message="Possible agreement error.", replacements=["have"])]
        return []


def test_analyse_gives_a_valid_record_with_feedback(fake_decode):
    fake_decode(seconds=10)
    asr = FakeASR([("Um,", 0.6), ("I", 0.9), ("has", 0.4), ("led", 0.9), ("three", 0.9), ("projects.", 0.9)])
    record = analyse(b"fake-audio", asr=asr, tool=FakeTool())

    audio, kwargs = asr.calls[0]
    assert isinstance(audio, np.ndarray)  # decoded in memory, never written to a file
    assert kwargs["allow_mock"] is False  # never mock text
    assert [(f["type"], f["text"]) for f in record["feedback"]] == [("filler", "Um,"), ("grammar", "has")]
    assert record["fluency"]["filler_count"] == 1
    assert io.validate(record) == []


def test_decode_gives_16khz_mono():
    import soundfile as sf

    buf = BytesIO()
    stereo_44k = np.zeros((44100, 2), dtype="float32")  # 1 s of stereo silence at 44.1 kHz
    sf.write(buf, stereo_44k, 44100, format="WAV")
    samples = decode(buf.getvalue())
    assert samples.ndim == 1 and samples.dtype == np.float32
    assert len(samples) == pipeline.SAMPLE_RATE


def test_unreadable_audio_raises_runtime_error():
    with pytest.raises(RuntimeError):
        decode(b"not audio")


def test_empty_words_are_dropped_and_reindexed():
    record = to_record({"model": "m", "transcript": "hi there",
                        "words": [{"i": 0, "word": "hi", "start": 0, "end": 0.2, "confidence": 0.9},
                                  {"i": 1, "word": "", "start": 0.2, "end": 0.3, "confidence": 0.1},
                                  {"i": 2, "word": "there", "start": 0.3, "end": 0.6, "confidence": 0.9}]})
    assert [(w["i"], w["word"]) for w in record["words"]] == [(0, "hi"), (1, "there")]


def test_whisper_wrapper_refuses_mock_when_asked():
    from src.asr.whisper_asr import WhisperASR

    asr = WhisperASR.__new__(WhisperASR)  # skip model loading
    asr.model, asr._backend, asr.model_size = None, "mock", "base"
    assert asr.transcribe("any.wav")["model"] == "mock-whisper"  # B's default behaviour kept
    with pytest.raises(RuntimeError, match="faster-whisper"):
        asr.transcribe(BytesIO(b"x"), allow_mock=False)


def test_whisper_wrapper_passes_memory_audio_and_language():
    from src.asr.whisper_asr import WhisperASR

    seen = {}

    class FakeModel:
        def transcribe(self, audio, **kwargs):
            seen["audio"], seen["kwargs"] = audio, kwargs
            word = SimpleNamespace(word=" Hello", start=0.0, end=0.4, probability=0.93)
            return [SimpleNamespace(text=" Hello", words=[word])], None

    asr = WhisperASR.__new__(WhisperASR)
    asr.model, asr._backend, asr.model_size = FakeModel(), "faster-whisper", "base"
    buf = BytesIO(b"x")
    result = asr.transcribe(buf)
    assert seen["audio"] is buf and seen["kwargs"]["language"] == "en"
    assert result["words"][0]["word"] == "Hello"