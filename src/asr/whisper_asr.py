"""Whisper ASR wrapper with word timestamps and confidence scores. Member B (WP2).

Uses faster-whisper or openai-whisper to extract:
- Verbatim transcript
- Word-level start and end timestamps
- Word-level confidence scores (probabilities)

Provides a mock/simulation fallback when run in lightweight or offline test environments.
The app calls transcribe(..., allow_mock=False), so it never shows feedback on mock text.
"""
from __future__ import annotations

from typing import Any, BinaryIO
import logging
from pathlib import Path
from typing import Any

from src.asr.normalisation import normalise_text

logger = logging.getLogger(__name__)


class WhisperASR:
    """Wrapper for Whisper / faster-whisper inference."""

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "float32"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._backend = None
        self._init_model()

    def _init_model(self) -> None:
        """Attempt to load faster-whisper or openai-whisper; fallback to mock mode if unavailable."""
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            self._backend = "faster-whisper"
            logger.info("Loaded faster-whisper model: %s", self.model_size)
            return
        except ImportError:
            pass

        try:
            import whisper
            self.model = whisper.load_model(self.model_size, device=self.device)
            self._backend = "openai-whisper"
            logger.info("Loaded openai-whisper model: %s", self.model_size)
            return
        except ImportError:
            pass

        self._backend = "mock"
        logger.info("Whisper packages not found. Operating in mock/simulation mode.")

    def transcribe(self, audio_path: str | Path | BinaryIO, fallback_text: str | None = None,
                   language: str | None = "en", allow_mock: bool = True) -> dict[str, Any]:
        """Transcribe audio and return transcript with word timestamps and confidences.

        audio_path: a file path, or (faster-whisper only) an in-memory file such as
            io.BytesIO, so the app never writes audio to disk.
        language: "en" by default; accented English can otherwise be detected as
            another language. None lets Whisper detect it.
        allow_mock: if False, raise instead of returning mock text when no Whisper
            package is installed (the app must never give feedback on mock text).
        """
        audio = str(audio_path) if isinstance(audio_path, (str, Path)) else audio_path

        if self._backend == "faster-whisper" and self.model is not None:
            segments, _ = self.model.transcribe(audio, word_timestamps=True, language=language)
            words = []
            full_text_chunks = []
            word_idx = 0
            for seg in segments:
                full_text_chunks.append(seg.text)
                if seg.words:
                    for w in seg.words:
                        words.append({
                            "i": word_idx,
                            "word": w.word.strip(),
                            "start": round(float(w.start), 3),
                            "end": round(float(w.end), 3),
                            "confidence": round(float(w.probability), 4),
                        })
                        word_idx += 1
            return {
                "source": "whisper",
                "model": f"faster-whisper-{self.model_size}",
                "transcript": " ".join(full_text_chunks).strip(),
                "words": words,
            }

        elif self._backend == "openai-whisper" and self.model is not None:
            if not isinstance(audio, str):
                raise TypeError("The openai-whisper backend needs a file path; install faster-whisper "
                                "to transcribe in-memory audio.")
            res = self.model.transcribe(audio, word_timestamps=True, language=language)
            words = []
            word_idx = 0
            for seg in res.get("segments", []):
                for w in seg.get("words", []):
                    words.append({
                        "i": word_idx,
                        "word": w.get("word", "").strip(),
                        "start": round(float(w.get("start", 0.0)), 3),
                        "end": round(float(w.get("end", 0.0)), 3),
                        "confidence": round(float(w.get("probability", 0.90)), 4),
                    })
                    word_idx += 1
            return {
                "source": "whisper",
                "model": f"openai-whisper-{self.model_size}",
                "transcript": res.get("text", "").strip(),
                "words": words,
            }

        if not allow_mock:
            raise RuntimeError("No Whisper package is installed (run: pip install faster-whisper), "
                               "so the audio cannot be transcribed.")

        # Mock / simulation mode (used in testing, demo fallback, or when audio file is simulated)
        text = fallback_text or "I have led three projects in my last job"
        raw_words = text.split()
        words = []
        cur_t = 0.5
        for i, w in enumerate(raw_words):
            dur = max(0.2, len(w) * 0.08)
            # Assign realistic confidence scores
            conf = 0.95 if w.lower() not in ["has", "led"] else 0.45
            words.append({
                "i": i,
                "word": w,
                "start": round(cur_t, 3),
                "end": round(cur_t + dur, 3),
                "confidence": conf,
            })
            cur_t += dur + 0.05

        return {
            "source": "whisper",
            "model": "mock-whisper",
            "transcript": text,
            "words": words,
        }