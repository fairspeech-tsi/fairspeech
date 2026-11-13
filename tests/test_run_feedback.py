"""Tests for the batch pipeline, with a fake LanguageTool (no Java needed)."""
import json
from types import SimpleNamespace

import pytest

from scripts.run_feedback import run
from src.feedback import io


class FakeTool:
    """Flags "has" after "I" as an agreement error, like LanguageTool's BASE_FORM rule."""

    def check(self, text):
        matches = []
        if text.startswith("I has"):
            matches.append(SimpleNamespace(rule_id="BASE_FORM", category="GRAMMAR", offset=2, error_length=3,
                                           message="Possible agreement error.", replacements=["have"]))
        return matches


def asr_record(segment_id, text, source="whisper"):
    """A contract-valid ASR record with simple timings and confidences."""
    words = [{"i": i, "word": w, "start": i * 0.4, "end": i * 0.4 + 0.3, "confidence": 0.9}
             for i, w in enumerate(text.split())]
    return {"schema_version": "0.1", "segment_id": segment_id, "source": source,
            "model": "openai/whisper-large-v3", "transcript": text, "words": words,
            "fluency": None, "feedback": [], "created_at": "2026-11-12T00:00:00Z"}


def write(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))


def test_pipeline_labels_saves_and_reports(tmp_path):
    asr_dir, out_dir = tmp_path / "asr", tmp_path / "out"
    write(asr_dir / "whisper" / "s1.json", asr_record("s1", "I has led three projects."))   # ASR error
    write(asr_dir / "whisper" / "s2.json", asr_record("s2", "Um, I think so."))             # filler on both sides
    write(asr_dir / "whisper" / "s3.json", asr_record("s3", "hello"))                       # not in the table
    (asr_dir / "whisper" / "s4.json").write_text("{not json")                               # broken file
    segments = {"s1": "I HAVE LED THREE PROJECTS", "s2": "UM I THINK SO", "s4": "YES"}

    stats = run(segments, asr_dir, out_dir, FakeTool())

    assert stats["segments"] == 3 and stats["asr_records"] == 2
    assert stats["no_human"] == 1 and stats["failed"] == 1
    assert (stats["false"], stats["genuine"]) == (1, 1)  # "has" false, "Um" genuine

    s1 = io.load(out_dir / "whisper" / "s1.json")
    assert [(f["text"], f["label"]) for f in s1["feedback"]] == [("has", "false")]
    assert s1["fluency"] is not None and io.validate(s1) == []
    human = io.load(out_dir / "human" / "s1.json")
    assert human["feedback"] == [] and human["fluency"] is None


def test_limit_and_rerun_are_safe(tmp_path):
    asr_dir, out_dir = tmp_path / "asr", tmp_path / "out"
    for seg in ("a", "b", "c"):
        write(asr_dir / "whisper" / f"{seg}.json", asr_record(seg, "I has led"))
    segments = {"a": "I HAVE LED", "b": "I HAVE LED", "c": "I HAVE LED"}

    assert run(segments, asr_dir, out_dir, FakeTool(), limit=2)["segments"] == 2
    run(segments, asr_dir, out_dir, FakeTool())
    run(segments, asr_dir, out_dir, FakeTool())  # a second full run must not duplicate flags
    a = io.load(out_dir / "whisper" / "a.json")
    assert len(a["feedback"]) == 1


def test_out_dir_inside_asr_dir_is_refused(tmp_path):
    asr_dir = tmp_path / "asr"
    write(asr_dir / "whisper" / "a.json", asr_record("a", "I has led"))
    for bad in (asr_dir, asr_dir / "feedback"):
        with pytest.raises(ValueError, match="--out-dir"):
            run({"a": "I HAVE LED"}, asr_dir, bad, FakeTool())
    assert io.load(asr_dir / "whisper" / "a.json")["feedback"] == []  # original untouched


def test_non_asr_folders_are_ignored(tmp_path):
    asr_dir, out_dir = tmp_path / "asr", tmp_path / "out"
    write(asr_dir / "whisper" / "a.json", asr_record("a", "I has led"))
    write(asr_dir / "human" / "a.json", asr_record("a", "I have led", source="human"))  # like B's second zip
    stats = run({"a": "I HAVE LED"}, asr_dir, out_dir, FakeTool())
    assert stats["asr_records"] == 1
    assert io.load(out_dir / "human" / "a.json")["transcript"] == "I HAVE LED"  # from the table, not the folder