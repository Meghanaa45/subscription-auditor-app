"""Price-change detection and savings estimation for detected subscriptions."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.core.detector import PERIODS_PER_YEAR, SubscriptionMatch

PRICE_CHANGE_THRESHOLD = 0.01  # 1% - ignores rounding noise, catches real changes


@dataclass
class PriceChangeEvent:
    date: pd.Timestamp
    old_amount: float
    new_amount: float
    pct_change: float


def price_change_events(match: SubscriptionMatch) -> list[PriceChangeEvent]:
    """Return every point in a subscription's history where the charged
    amount changed by more than the noise threshold, most recent last."""
    events: list[PriceChangeEvent] = []
    for i in range(1, len(match.amounts)):
        old, new = match.amounts[i - 1], match.amounts[i]
        if old == 0:
            continue
        pct_change = (new - old) / old
        if abs(pct_change) > PRICE_CHANGE_THRESHOLD:
            events.append(
                PriceChangeEvent(
                    date=match.dates[i],
                    old_amount=old,
                    new_amount=new,
                    pct_change=round(pct_change * 100, 1),
                )
            )
    return events


def savings_summary(matches: list[SubscriptionMatch]) -> dict:
    """Summarize total recurring spend and the potential savings from
    cancelling each detected subscription."""
    by_category: dict[str, float] = {}
    for m in matches:
        by_category[m.category] = round(by_category.get(m.category, 0.0) + m.annual_cost, 2)

    price_increases = [m for m in matches if m.price_increased]
    increase_annual_impact = 0.0
    for m in price_increases:
        periods_per_year = PERIODS_PER_YEAR[m.period]
        increase_annual_impact += (m.last_amount - m.first_amount) * periods_per_year

    return {
        "total_subscriptions": len(matches),
        "total_annual_cost": round(sum(m.annual_cost for m in matches), 2),
        "total_monthly_cost": round(sum(m.monthly_cost for m in matches), 2),
        "annual_cost_by_category": by_category,
        "subscriptions_with_price_increases": len(price_increases),
        "annual_cost_added_by_price_increases": round(increase_annual_impact, 2),
    }
