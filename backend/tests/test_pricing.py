import pandas as pd

from app.core.detector import SubscriptionMatch
from app.core.pricing import price_change_events, savings_summary


def _match(amounts, period_days=30, category="software"):
    dates = pd.date_range("2024-01-01", periods=len(amounts), freq="MS")
    return SubscriptionMatch(
        merchant="Test Merchant",
        category=category,
        period="monthly",
        period_days=period_days,
        occurrences=len(amounts),
        first_date=dates[0],
        last_date=dates[-1],
        amounts=amounts,
        dates=list(dates),
        interval_match_ratio=1.0,
        confidence=0.95,
        price_increased=amounts[-1] > amounts[0] * 1.03,
        first_amount=amounts[0],
        last_amount=amounts[-1],
    )


def test_price_change_events_detects_single_increase():
    match = _match([10.0, 10.0, 10.0, 12.0, 12.0])
    events = price_change_events(match)
    assert len(events) == 1
    assert events[0].old_amount == 10.0
    assert events[0].new_amount == 12.0
    assert events[0].pct_change == 20.0


def test_price_change_events_ignores_rounding_noise():
    match = _match([10.00, 10.001, 9.999, 10.00])
    events = price_change_events(match)
    assert events == []


def test_savings_summary_totals():
    matches = [_match([10.0] * 4, category="streaming"), _match([20.0] * 4, category="fitness")]
    summary = savings_summary(matches)
    assert summary["total_subscriptions"] == 2
    assert summary["total_annual_cost"] == round(10.0 * 12 + 20.0 * 12, 2)
    assert summary["annual_cost_by_category"]["streaming"] == round(10.0 * 12, 2)


def test_savings_summary_counts_price_increases():
    increased = _match([10.0, 10.0, 13.0])
    flat = _match([10.0, 10.0, 10.0])
    summary = savings_summary([increased, flat])
    assert summary["subscriptions_with_price_increases"] == 1
