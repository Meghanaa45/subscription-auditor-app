"""Evaluate detector accuracy against labeled ground truth.

Used with the synthetic dataset generator (scripts/generate_synthetic_data.py),
which knows which merchants are genuinely recurring subscriptions and which
are one-off or irregular "noise" charges. This lets us report real precision/
recall numbers instead of eyeballing the output.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.core.detector import SubscriptionMatch


@dataclass
class EvaluationResult:
    precision: float
    recall: float
    f1: float
    true_positives: list[str]
    false_positives: list[str]
    false_negatives: list[str]


def evaluate_detections(
    matches: list[SubscriptionMatch],
    ground_truth: pd.DataFrame,
) -> EvaluationResult:
    """Compare detected subscriptions against ground truth.

    `ground_truth` must have columns: merchant, is_subscription (bool),
    at the per-merchant level (one row per unique merchant in the source
    dataset, matching the canonical names produced by normalize_merchants).
    """
    detected_merchants = {m.merchant for m in matches}
    true_subscription_merchants = set(
        ground_truth.loc[ground_truth["is_subscription"], "merchant"]
    )
    all_known_merchants = set(ground_truth["merchant"])

    true_positives = sorted(detected_merchants & true_subscription_merchants)
    false_positives = sorted(detected_merchants - true_subscription_merchants)
    false_negatives = sorted(true_subscription_merchants - detected_merchants)

    tp, fp, fn = len(true_positives), len(false_positives), len(false_negatives)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    del all_known_merchants  # kept for potential future per-merchant breakdown

    return EvaluationResult(
        precision=round(precision, 3),
        recall=round(recall, 3),
        f1=round(f1, 3),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )
