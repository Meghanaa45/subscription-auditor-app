from __future__ import annotations

from app.agent.tools import (
    get_savings_summary,
    get_subscription_detail,
    get_subscriptions_with_price_increases,
    get_top_subscriptions_by_cost,
    list_subscriptions,
)

SAMPLE_REPORT = {
    "summary": {
        "total_subscriptions": 2,
        "total_annual_cost": 350.0,
        "total_monthly_cost": 29.17,
        "annual_cost_by_category": {"streaming": 200.0, "software": 150.0},
        "subscriptions_with_price_increases": 1,
        "annual_cost_added_by_price_increases": 20.0,
    },
    "subscriptions": [
        {
            "merchant": "Netflix",
            "category": "streaming",
            "estimated_annual_cost": 200.0,
            "price_increased": True,
            "price_change_events": [{"date": "2024-06-01", "old_amount": 15.0, "new_amount": 17.0, "pct_change": 13.3}],
        },
        {
            "merchant": "Notion",
            "category": "software",
            "estimated_annual_cost": 150.0,
            "price_increased": False,
            "price_change_events": [],
        },
    ],
}


def test_list_subscriptions_returns_all():
    assert len(list_subscriptions(SAMPLE_REPORT)) == 2


def test_get_subscription_detail_case_insensitive():
    result = get_subscription_detail(SAMPLE_REPORT, "netflix")
    assert result["merchant"] == "Netflix"


def test_get_subscription_detail_unknown_merchant_returns_error_with_options():
    result = get_subscription_detail(SAMPLE_REPORT, "Hulu")
    assert "error" in result
    assert "Netflix" in result["available_merchants"]


def test_get_savings_summary_passthrough():
    assert get_savings_summary(SAMPLE_REPORT) == SAMPLE_REPORT["summary"]


def test_get_top_subscriptions_by_cost_respects_limit():
    top = get_top_subscriptions_by_cost(SAMPLE_REPORT, limit=1)
    assert len(top) == 1
    assert top[0]["merchant"] == "Netflix"


def test_get_subscriptions_with_price_increases_filters():
    increased = get_subscriptions_with_price_increases(SAMPLE_REPORT)
    assert len(increased) == 1
    assert increased[0]["merchant"] == "Netflix"
