"""Run the feedback pipeline on ASR outputs and label every flag for the gate.

For each segment, the human transcript (from the segment table) and every ASR
record of that segment (from B) get grammar and filler flags; ASR records also
get fluency. The alignment module then labels each ASR flag false, genuine or
ambiguous against the human record. All records are saved in the shared JSON
format, so B's gate reads the labels directly from them.

Inputs:
    segment table (CSV)              one row per segment: segment_id + human transcript
    <asr-dir>/<source>/<id>.json     ASR records from B (contract format, no feedback yet)
Outputs:
    <out-dir>/<source>/<id>.json     feedback records, human and ASR, with labels

Usage (from the repo root):
    python -m scripts.run_feedback --segments data/interim/gold_dataset.csv \\
        --asr-dir data/processed/asr --out-dir data/processed/feedback --limit 20

A file that fails (invalid JSON, schema error) is reported and skipped, so one
bad file does not stop a batch of thousands.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.feedback import io
from src.feedback.alignment import label_flags
from src.feedback.filler import add_filler_feedback
from src.feedback.fluency import add_fluency
from src.feedback.grammar import add_grammar_feedback

ASR_SOURCES = ("whisper", "crisperwhisper", "vosk")

def human_record(segment_id: str, text: str) -> dict:
    """A contract record for a human transcript: one word per token, no timings."""
    words = [{"i": i, "word": w, "start": None, "end": None, "confidence": None}
             for i, w in enumerate(text.split())]
    return {
        "schema_version": "0.1",
        "segment_id": segment_id,
        "source": "human",
        "model": None,
        "transcript": text,
        "words": words,
        "fluency": None,
        "feedback": [],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def read_segments(path: Path, id_col: str, text_col: str) -> dict[str, str]:
    """{segment_id: human transcript} from the segment table."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row[id_col]: row[text_col] for row in csv.DictReader(f)}


def check_dirs(asr_dir: Path, out_dir: Path) -> None:
    """Refuse an output folder that is, or is inside, the ASR folder.

    Writing there would overwrite B's original files and mix outputs with inputs.
    """
    asr, out = asr_dir.resolve(), out_dir.resolve()
    if out == asr or asr in out.parents:
        raise ValueError(f"--out-dir must be outside --asr-dir ({asr_dir})")


def find_asr_records(asr_dir: Path) -> tuple[dict[str, list[Path]], list[str]]:
    """ASR record files grouped by segment id (the file name without .json).

    Only the subfolders in ASR_SOURCES are read. Returns the records and the
    names of the subfolders that were skipped.
    """
    by_segment = defaultdict(list)
    skipped = []
    for folder in sorted(p for p in asr_dir.iterdir() if p.is_dir()):
        if folder.name not in ASR_SOURCES:
            skipped.append(folder.name)
            continue
        for path in sorted(folder.glob("*.json")):
            by_segment[path.stem].append(path)
    return dict(by_segment), skipped


def process_segment(segment_id: str, human_text: str, asr_paths: list[Path],
                    out_dir: Path, tool, stats: Counter) -> None:
    """Add feedback to the human record and each ASR record, label, and save."""
    human = human_record(segment_id, human_text)
    stats["unmapped"] += add_grammar_feedback(human, tool)
    add_filler_feedback(human)
    io.save(human, out_dir / "human" / f"{segment_id}.json")

    for path in asr_paths:
        try:
            asr = io.load(path)
            asr["feedback"] = []
            stats["unmapped"] += add_grammar_feedback(asr, tool)
            add_filler_feedback(asr)
            add_fluency(asr)
            stats.update(label_flags(human, asr))
            io.save(asr, out_dir / asr["source"] / f"{segment_id}.json")
            stats["asr_records"] += 1
        except (ValueError, KeyError) as err:
            stats["failed"] += 1
            print(f"  skipped {path}: {str(err).splitlines()[0]}")


def run(segments: dict[str, str], asr_dir: Path, out_dir: Path, tool,
        limit: int | None = None) -> Counter:
    """Process every segment that has ASR records. Returns counts for the summary."""
    check_dirs(asr_dir, out_dir)
    stats: Counter = Counter()
    asr_files, skipped = find_asr_records(asr_dir)
    for name in skipped:
        print(f"  ignored folder {asr_dir / name}: not one of {', '.join(ASR_SOURCES)}")
    stats["no_human"] = sum(1 for seg in asr_files if seg not in segments)

    todo = [seg for seg in sorted(asr_files) if seg in segments]
    for n, segment_id in enumerate(todo[:limit], 1):
        process_segment(segment_id, segments[segment_id], asr_files[segment_id], out_dir, tool, stats)
        stats["segments"] += 1
        if n % 100 == 0:
            print(f"  {n}/{len(todo[:limit])} segments")
    return stats


def main() -> None:
    import language_tool_python

    ap = argparse.ArgumentParser(description="Run feedback modules and label ASR flags.")
    ap.add_argument("--segments", type=Path, required=True, help="segment table CSV")
    ap.add_argument("--asr-dir", type=Path, required=True, help="folder with <source>/<id>.json ASR records")
    ap.add_argument("--out-dir", type=Path, required=True, help="where feedback records are written")
    ap.add_argument("--id-column", default="segment_id")
    ap.add_argument("--text-column", default="text", help="human transcript column")
    ap.add_argument("--limit", type=int, help="process only the first N segments (pilot runs)")
    args = ap.parse_args()

    try:
        check_dirs(args.asr_dir, args.out_dir)  # before starting LanguageTool
    except ValueError as err:
        ap.error(str(err))

    segments = read_segments(args.segments, args.id_column, args.text_column)
    tool = language_tool_python.LanguageTool("en-US")
    try:
        stats = run(segments, args.asr_dir, args.out_dir, tool, args.limit)
    finally:
        tool.close()

    print(f"\nSegments: {stats['segments']}  ASR records: {stats['asr_records']}  failed: {stats['failed']}")
    print(f"Labels: false {stats['false']}  genuine {stats['genuine']}  ambiguous {stats['ambiguous']}")
    print(f"Unmapped matches: {stats['unmapped']}  ASR segments missing from the table: {stats['no_human']}")


if __name__ == "__main__":
    main()