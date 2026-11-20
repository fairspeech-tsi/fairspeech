"""Turn a recorded or uploaded answer into a feedback record, in memory only.

audio bytes -> 16 kHz mono array -> B's Whisper wrapper (local, small model)
-> contract record -> grammar, filler and fluency modules (C). Nothing is
written to disk: the audio is decoded in memory, passed to Whisper as an
array, and the record is kept in the Streamlit session (data notice, MO2).
"""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

import numpy as np
import streamlit as st

from src.feedback.filler import add_filler_feedback
from src.feedback.fluency import add_fluency
from src.feedback.grammar import add_grammar_feedback

# Small enough to run on a laptop CPU in a few seconds per answer.
ASR_MODEL_SIZE = "base"
SAMPLE_RATE = 16000  # Whisper works on 16 kHz mono audio


def decode(audio: bytes) -> np.ndarray:
    """Decode recorded or uploaded audio (wav, mp3, flac, ogg) to 16 kHz mono, in memory.

    Uses soundfile instead of faster-whisper's own decoder, which breaks with
    recent PyAV versions (TypeError: unexpected keyword 'metadata_errors').
    Raises soundfile's LibsndfileError (a RuntimeError) for unreadable files.
    """
    import librosa
    import soundfile as sf

    data, rate = sf.read(BytesIO(audio), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if rate != SAMPLE_RATE:
        mono = librosa.resample(mono, orig_sr=rate, target_sr=SAMPLE_RATE)
    return mono.astype(np.float32)


@st.cache_resource(show_spinner="Loading the speech recogniser (first time only)…")
def get_asr():
    """One Whisper model per app process (loading takes a few seconds)."""
    from src.asr.whisper_asr import WhisperASR

    return WhisperASR(model_size=ASR_MODEL_SIZE, device="cpu", compute_type="int8")


@st.cache_resource(show_spinner="Starting the grammar checker (first time only)…")
def get_grammar_tool():
    """One local LanguageTool server per app process."""
    import language_tool_python

    return language_tool_python.LanguageTool("en-US")


def to_record(asr_result: dict) -> dict:
    """Wrap the ASR output in the shared contract format (empty words removed)."""
    words = [w for w in asr_result["words"] if w["word"]]
    for i, w in enumerate(words):
        w["i"] = i
    return {
        "schema_version": "0.1",
        "segment_id": "app-answer",
        "source": "whisper",
        "model": asr_result["model"],
        "transcript": asr_result["transcript"],
        "words": words,
        "fluency": None,
        "feedback": [],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def analyse(audio: bytes, asr=None, tool=None) -> dict:
    """Transcribe one answer and add grammar, filler and fluency feedback.

    asr and tool can be passed in by tests; the app uses the cached ones.
    Raises RuntimeError for unreadable audio or if no Whisper package is
    installed (never mock text).
    """
    asr = asr or get_asr()
    tool = tool or get_grammar_tool()
    record = to_record(asr.transcribe(decode(audio), allow_mock=False))
    add_grammar_feedback(record, tool)
    add_filler_feedback(record)
    add_fluency(record)
    return record