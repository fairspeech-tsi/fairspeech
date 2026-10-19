"""Grammar module (LanguageTool + spaCy). Week 1-2.

Input: a record with `transcript` and `words`.
Output: grammar flags appended to `record["feedback"]` (type "grammar").
"""
from __future__ import annotations

from typing import Any


def detect_grammar(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return grammar flags for one transcript, mapped to word indices."""
    raise NotImplementedError("TODO (C): LanguageTool check + map character offsets to word indices")
