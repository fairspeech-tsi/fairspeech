"""Train the feedback gate. Weeks 5-6.

- Baseline: global confidence threshold (threshold sweep).
- Models: logistic regression (L2) and LightGBM.
- Grouped 5-fold cross-validation (groups = conversations) on the training split only.
- Class weights, plus sample weights so each accent group contributes equally.
- Decision threshold chosen on the validation split so genuine-flag recall >= 0.90.
"""
from __future__ import annotations

import pandas as pd


def train_gate(features: pd.DataFrame, segments: pd.DataFrame):
    """Fit the models on the training split and return the chosen model and threshold."""
    raise NotImplementedError("TODO (B)")
