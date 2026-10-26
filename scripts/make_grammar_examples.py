"""Write example grammar outputs for human/Whisper sentence pairs.

The pairs are hand-written to mimic common ASR errors on accented speech, so the
expected label of every flag is known. Used by A (RQ1 analysis), D (docs) and C
(alignment tests) until real pilot data is processed.

Usage (from the repo root):
    python -m scripts.make_grammar_examples
"""
from datetime import datetime, timezone
from pathlib import Path

import language_tool_python

from src.feedback import io
from src.feedback.grammar import add_grammar_feedback

OUT_DIR = Path("data/mock/grammar_examples")

# (segment_id, human transcript, Whisper transcript, index of the misrecognised
# word or None, expected label of the Whisper grammar flag)
PAIRS = [
    ("mock_pair1", "I have led three projects in my last job",
     "I has led three projects in my last job.", 1, "false"),
    ("mock_pair2", "she works in a bank in the city centre",
     "She work in a bank in the city centre.", 1, "false"),
    ("mock_pair3", "we discussed an idea with the whole team",
     "We discussed a idea with the whole team.", 2, "false"),
    ("mock_pair4", "he don't like the weekly meetings",
     "He don't like the weekly meetings.", None, "genuine"),
    ("mock_pair5", "um I think the deadline was too short",
     "Um, I think the deadline was too short.", None, "no flag"),
]


def make_record(segment_id: str, source: str, text: str, low_conf_index: int | None) -> dict:
    """Build a contract record. Whisper words get a high confidence, except the
    misrecognised word, which gets a low one, as a real ASR error would."""
    words = []
    for i, w in enumerate(text.split()):
        if source == "human":
            conf = None
        else:
            conf = 0.42 if i == low_conf_index else 0.95
        words.append({"i": i, "word": w, "start": None, "end": None, "confidence": conf})
    return {
        "schema_version": "0.1",
        "segment_id": segment_id,
        "source": source,
        "model": None if source == "human" else "openai/whisper-large-v3",
        "transcript": text,
        "words": words,
        "fluency": None,
        "feedback": [],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main() -> None:
    tool = language_tool_python.LanguageTool("en-US")
    try:
        for seg_id, human_text, asr_text, low_i, expected in PAIRS:
            for source, text, low in (("human", human_text, None), ("whisper", asr_text, low_i)):
                rec = make_record(seg_id, source, text, low)
                add_grammar_feedback(rec, tool)
                io.save(rec, OUT_DIR / source / f"{seg_id}.json")
                flags = [(f["text"], f["category"]) for f in rec["feedback"]]
                print(f"{seg_id:11} {source:8} {flags}")
            print(f"{'':11} expected: {expected}\n")
    finally:
        tool.close()


if __name__ == "__main__":
    main()