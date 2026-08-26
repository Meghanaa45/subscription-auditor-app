"""Detect recurring charges (subscriptions) from normalized transaction data.

Approach: for each merchant, look at the sequence of charge dates and
amounts. A merchant is flagged as a subscription if its charges repeat at a
consistent interval (within a tolerance window that scales with the period
length) for a minimum number of occurrences. This is deliberately a
transparent, rule-based approach rather than a black box, so every
classification can be explained by the interval and amount evidence behind it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Candidate billing periods in days, with the day-tolerance allowed for a
# charge to still count as landing "on schedule". Tolerance scales with
# period length since longer periods drift more (e.g. "the 31st" doesn't
# exist in February).
CANDIDATE_PERIODS: list[tuple[str, int, int]] = [
    ("weekly", 7, 2),
    ("biweekly", 14, 3),
    ("monthly", 30, 4),
    ("quarterly", 91, 6),
    ("annual", 365, 10),
]

MIN_OCCURRENCES = 3
MIN_INTERVAL_MATCH_RATIO = 0.7  # fraction of gaps that must match the period
MAX_AMOUNT_COEFFICIENT_OF_VARIATION = 0.35  # allows for price increases, not random amounts

# True number of billing cycles per year for each period. Using this instead
# of 365/period_days avoids overcounting: a "monthly" charge should be
# annualized as x12, not x(365/30)=x12.17, since real monthly billing happens
# exactly 12 times a year regardless of the day-count approximation used for
# interval matching.
PERIODS_PER_YEAR = {
    "weekly": 52,
    "biweekly": 26,
    "monthly": 12,
    "quarterly": 4,
    "annual": 1,
}


@dataclass
class SubscriptionMatch:
    merchant: str
    category: str
    period: str
    period_days: int
    occurrences: int
    first_date: pd.Timestamp
    last_date: pd.Timestamp
    amounts: list[float]
    dates: list[pd.Timestamp]
    interval_match_ratio: float
    confidence: float
    price_increased: bool = field(default=False)
    first_amount: float = field(default=0.0)
    last_amount: float = field(default=0.0)

    @property
    def monthly_cost(self) -> float:
        periods_per_year = PERIODS_PER_YEAR[self.period]
        return round((self.last_amount * periods_per_year) / 12.0, 2)

    @property
    def annual_cost(self) -> float:
        periods_per_year = PERIODS_PER_YEAR[self.period]
        return round(self.last_amount * periods_per_year, 2)


def _best_period_match(gaps: np.ndarray) -> tuple[str, int, float] | None:
    """Return (period_name, period_days, match_ratio) for the candidate
    period whose tolerance window matches the largest fraction of gaps,
    provided that fraction clears MIN_INTERVAL_MATCH_RATIO."""
    best: tuple[str, int, float] | None = None
    for name, period_days, tolerance in CANDIDATE_PERIODS:
        matches = np.abs(gaps - period_days) <= tolerance
        ratio = matches.mean() if len(gaps) else 0.0
        if ratio >= MIN_INTERVAL_MATCH_RATIO and (best is None or ratio > best[2]):
            best = (name, period_days, ratio)
    return best


def _amount_coefficient_of_variation(amounts: np.ndarray) -> float:
    mean = amounts.mean()
    if mean == 0:
        return float("inf")
    return float(amounts.std() / mean)


def detect_subscriptions(normalized_transactions: pd.DataFrame) -> list[SubscriptionMatch]:
    """Scan normalized transactions (must have merchant, category, date,
    amount columns) and return the list of detected subscriptions."""
    matches: list[SubscriptionMatch] = []

    for merchant, group in normalized_transactions.groupby("merchant"):
        group = group.sort_values("date")
        dates = group["date"].tolist()
        amounts = group["amount"].to_numpy()

        if len(dates) < MIN_OCCURRENCES:
            continue

        gaps = np.array([(dates[i] - dates[i - 1]).days for i in range(1, len(dates))])
        period_match = _best_period_match(gaps)
        if period_match is None:
            continue
        period_name, period_days, interval_ratio = period_match

        cov = _amount_coefficient_of_variation(amounts)
        if cov > MAX_AMOUNT_COEFFICIENT_OF_VARIATION:
            continue

        # Confidence blends interval regularity and amount stability; both
        # matter for calling something a genuine subscription vs. a habit.
        amount_stability = max(0.0, 1.0 - cov / MAX_AMOUNT_COEFFICIENT_OF_VARIATION)
        confidence = round(0.6 * interval_ratio + 0.4 * amount_stability, 3)

        first_amount, last_amount = float(amounts[0]), float(amounts[-1])
        price_increased = last_amount > first_amount * 1.03  # >3% counts as a real increase

        matches.append(
            SubscriptionMatch(
                merchant=merchant,
                category=group["category"].iloc[0],
                period=period_name,
                period_days=period_days,
                occurrences=len(dates),
                first_date=dates[0],
                last_date=dates[-1],
                amounts=[float(a) for a in amounts],
                dates=dates,
                interval_match_ratio=round(float(interval_ratio), 3),
                confidence=confidence,
                price_increased=price_increased,
                first_amount=first_amount,
                last_amount=last_amount,
            )
        )

    return sorted(matches, key=lambda m: m.annual_cost, reverse=True)


def total_estimated_annual_cost(matches: list[SubscriptionMatch]) -> float:
    return round(sum(m.annual_cost for m in matches), 2)
