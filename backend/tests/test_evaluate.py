import pandas as pd

from app.core.detector import SubscriptionMatch
from app.core.evaluate import evaluate_detections


def _match(merchant):
    dates = pd.date_range("2024-01-01", periods=3, freq="MS")
    return SubscriptionMatch(
        merchant=merchant,
        category="software",
        period="monthly",
        period_days=30,
        occurrences=3,
        first_date=dates[0],
        last_date=dates[-1],
        amounts=[10.0, 10.0, 10.0],
        dates=list(dates),
        interval_match_ratio=1.0,
        confidence=0.9,
        first_amount=10.0,
        last_amount=10.0,
    )


def test_perfect_detection_scores_1():
    matches = [_match("Netflix"), _match("Spotify")]
    ground_truth = pd.DataFrame(
        {"merchant": ["Netflix", "Spotify", "Random Store"], "is_subscription": [True, True, False]}
    )
    result = evaluate_detections(matches, ground_truth)
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0


def test_false_positive_reduces_precision():
    matches = [_match("Netflix"), _match("Random Store")]
    ground_truth = pd.DataFrame(
        {"merchant": ["Netflix", "Random Store"], "is_subscription": [True, False]}
    )
    result = evaluate_detections(matches, ground_truth)
    assert result.precision == 0.5
    assert result.recall == 1.0
    assert result.false_positives == ["Random Store"]


def test_missed_subscription_reduces_recall():
    matches = [_match("Netflix")]
    ground_truth = pd.DataFrame(
        {"merchant": ["Netflix", "Spotify"], "is_subscription": [True, True]}
    )
    result = evaluate_detections(matches, ground_truth)
    assert result.recall == 0.5
    assert result.false_negatives == ["Spotify"]
