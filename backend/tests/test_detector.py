import pandas as pd

from app.core.detector import detect_subscriptions


def _monthly_series(merchant, category, amount, months=6, day=1, amount_step=0.0):
    dates = pd.date_range("2024-01-01", periods=months, freq="MS") + pd.Timedelta(days=day - 1)
    return pd.DataFrame(
        {
            "date": dates,
            "merchant": merchant,
            "category": category,
            "amount": [round(amount + i * amount_step, 2) for i in range(months)],
        }
    )


def test_detects_consistent_monthly_charge():
    df = _monthly_series("Netflix", "streaming", 15.49, months=6)
    matches = detect_subscriptions(df)
    assert len(matches) == 1
    assert matches[0].merchant == "Netflix"
    assert matches[0].period == "monthly"


def test_ignores_charges_below_minimum_occurrences():
    df = _monthly_series("Netflix", "streaming", 15.49, months=2)
    matches = detect_subscriptions(df)
    assert matches == []


def test_ignores_irregular_intervals():
    dates = pd.to_datetime(["2024-01-01", "2024-01-09", "2024-01-31", "2024-02-25", "2024-03-30"])
    df = pd.DataFrame(
        {
            "date": dates,
            "merchant": "Blue Bottle Coffee",
            "category": "uncategorized",
            "amount": [5.25, 7.80, 4.50, 6.10, 8.75],
        }
    )
    matches = detect_subscriptions(df)
    assert matches == []


def test_ignores_wildly_varying_amounts():
    dates = pd.date_range("2024-01-01", periods=6, freq="MS")
    df = pd.DataFrame(
        {
            "date": dates,
            "merchant": "Random Store",
            "category": "uncategorized",
            "amount": [10.0, 80.0, 15.0, 120.0, 8.0, 200.0],
        }
    )
    matches = detect_subscriptions(df)
    assert matches == []


def test_flags_price_increase():
    df = _monthly_series("Adobe Creative Cloud", "software", 52.99, months=8, amount_step=0.0)
    df.loc[df.index >= 4, "amount"] = 59.99
    matches = detect_subscriptions(df)
    assert len(matches) == 1
    assert matches[0].price_increased is True


def test_detects_weekly_period():
    dates = pd.date_range("2024-01-01", periods=8, freq="7D")
    df = pd.DataFrame(
        {
            "date": dates,
            "merchant": "Meal Kit Co",
            "category": "uncategorized",
            "amount": [59.99] * 8,
        }
    )
    matches = detect_subscriptions(df)
    assert len(matches) == 1
    assert matches[0].period == "weekly"


def test_annual_cost_uses_latest_amount():
    df = _monthly_series("Spotify", "streaming", 9.99, months=5)
    df.loc[df.index == 4, "amount"] = 10.99
    matches = detect_subscriptions(df)
    assert matches[0].last_amount == 10.99
    assert matches[0].annual_cost == round(10.99 * 12, 2)
