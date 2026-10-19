"""False feedback rate, group gap and genuine-flag recall. Week 3.

Definitions follow the proposal (Appendix B) and docs/data_contracts.md.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping


def false_feedback_rate(records: Iterable[dict[str, Any]]) -> float:
    """FFR = flags shown and labelled "false" / all flags shown (ambiguous flags excluded)."""
    raise NotImplementedError("TODO (C)")


def group_gap(ffr_by_group: Mapping[str, float]) -> float:
    """Gap = max FFR_g - min FFR_g across accent groups."""
    raise NotImplementedError("TODO (C)")


def genuine_flag_recall(records: Iterable[dict[str, Any]]) -> float:
    """Kept genuine flags / all genuine flags (shown == True counts as kept)."""
    raise NotImplementedError("TODO (C)")


def missed_real_error_rate(records: Iterable[dict[str, Any]]) -> float:
    """1 - genuine_flag_recall: share of genuine flags hidden by the gate."""
    raise NotImplementedError("TODO (C)")
