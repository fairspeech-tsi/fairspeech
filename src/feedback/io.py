"""Load, save and validate transcript + feedback JSON files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "feedback.schema.json"


def load_schema() -> dict[str, Any]:
    """Return the feedback JSON schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate(record: dict[str, Any]) -> list[str]:
    """Return a list of validation error messages (empty if the record is valid)."""
    validator = Draft202012Validator(load_schema())
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in validator.iter_errors(record)]


def load(path: str | Path) -> dict[str, Any]:
    """Load one feedback JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(record: dict[str, Any], path: str | Path) -> None:
    """Validate and save one feedback JSON file."""
    errors = validate(record)
    if errors:
        raise ValueError("Invalid feedback record:\n" + "\n".join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
