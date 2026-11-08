"""Metrics: false feedback rate, gap between groups and genuine-flag recall.

Owner: C. Works on ASR records labelled by the alignment module. The same
functions give RQ1 (before gating: every flag has shown = True) and RQ2
(after gating: B's gate sets shown = False on suppressed flags).
Definitions: docs/data_contracts.md, "Metric definitions".
"""
from __future__ import annotations

LABELLED_TYPES = {"grammar", "filler"}


def flag_rows(records: list[dict], groups: dict[str, str]) -> list[dict]:
    """One row per labelled grammar or filler flag.

    Each row is {"group", "label", "shown", "type", "category"}, where group
    comes from groups[record["segment_id"]]. Flags without a label (alignment
    has not run) are skipped. A segment missing from groups raises KeyError.
    """
    rows = []
    for rec in records:
        group = groups[rec["segment_id"]]
        for f in rec.get("feedback", []):
            if f["type"] not in LABELLED_TYPES or f["label"] is None:
                continue
            rows.append({
                "group": group,
                "label": f["label"],
                "shown": f["shown"],
                "type": f["type"],
                "category": f["category"],
            })
    return rows


def _count_shown(rows: list[dict]) -> dict[str, int]:
    """Number of shown flags per label: {"false": n, "genuine": n, "ambiguous": n}.

    An unexpected label raises KeyError instead of being dropped silently.
    """
    counts = {"false": 0, "genuine": 0, "ambiguous": 0}
    for r in rows:
        if r["shown"]:
            counts[r["label"]] += 1
    return counts


def false_feedback_rate(rows: list[dict]) -> float | None:
    """Share of false flags among the flags shown (ambiguous excluded).

    FFR = shown false / (shown false + shown genuine). Returns None if no
    false or genuine flag is shown, so an empty group is not reported as 0.
    """
    c = _count_shown(rows)
    total = c["false"] + c["genuine"]
    return None if total == 0 else c["false"] / total


def ffr_by_group(rows: list[dict]) -> dict[str, float | None]:
    """False feedback rate for each group in rows, keyed by group name (sorted)."""
    groups = {r["group"] for r in rows}
    return {
        group: false_feedback_rate([r for r in rows if r["group"] == group])
        for group in sorted(groups)
    }


def group_gap(rates: dict[str, float | None]) -> float | None:
    """Gap = highest FFR minus lowest FFR, ignoring groups whose FFR is None.

    Returns None if fewer than two groups have an FFR.
    """
    valid_rates = [r for r in rates.values() if r is not None]
    if len(valid_rates) < 2:
        return None
    return max(valid_rates) - min(valid_rates)


def genuine_flag_recall(rows: list[dict]) -> float | None:
    """Share of genuine flags that are shown: shown genuine / all genuine.

    1.0 before gating. The gate threshold keeps it at least 0.90 on the
    validation set. Returns None if there are no genuine flags.
    """
    n_all = sum(1 for r in rows if r["label"] == "genuine")
    if n_all == 0:
        return None
    return _count_shown(rows)["genuine"] / n_all


def missed_real_error_rate(rows: list[dict]) -> float | None:
    """Share of genuine flags hidden by the gate: 1 - genuine_flag_recall."""
    recall = genuine_flag_recall(rows)
    return None if recall is None else 1 - recall


def ambiguous_share(rows: list[dict]) -> float | None:
    """Share of ambiguous flags among all flags shown. None if none are shown."""
    c = _count_shown(rows)
    total = sum(c.values())
    return None if total == 0 else c["ambiguous"] / total


def ffr_bounds(rows: list[dict]) -> tuple[float, float] | None:
    """FFR if every shown ambiguous flag were genuine (low) or false (high).

    low  = shown false / shown (false + genuine + ambiguous)
    high = shown (false + ambiguous) / shown (false + genuine + ambiguous)
    Returns None if no flag is shown.
    """
    c = _count_shown(rows)
    total = sum(c.values())
    if total == 0:
        return None
    return c["false"] / total, (c["false"] + c["ambiguous"]) / total