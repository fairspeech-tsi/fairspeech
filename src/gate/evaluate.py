"""Evaluate the gate on the test split. Week 6.

Reports precision, recall, PR-AUC and ROC-AUC for false flags; FFR per accent group
before and after gating; the gap; genuine-flag recall; leave-one-accent-out results;
ablations (no confidence features, no cross-model agreement); SHAP importance
(descriptive, not causal). Confidence intervals: speaker-level bootstrap, 1,000 resamples.
"""
from __future__ import annotations


def evaluate_gate(*args, **kwargs):
    """Return a results table for A's RQ2 analysis."""
    raise NotImplementedError("TODO (B)")
