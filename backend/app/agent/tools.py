"""Tools the agent can call, each operating only on the already-computed
report for one audit (see app.core.report.build_report_dict). The model
never receives raw transaction data or generates numbers itself - every
figure it discusses must come back through one of these functions, so
answers stay grounded in what the detector actually found.
"""

from __future__ import annotations

from typing import Any, Callable

Report = dict[str, Any]


def list_subscriptions(report: Report) -> list[dict]:
    """Return every detected subscription with its cost, category, and
    confidence. Use this first to see what's available before answering
    questions about specific merchants."""
    return report["subscriptions"]


def get_subscription_detail(report: Report, merchant: str) -> dict:
    """Return full detail (including price-change history) for one merchant.
    `merchant` should match a name from list_subscriptions."""
    for sub in report["subscriptions"]:
        if sub["merchant"].lower() == merchant.lower():
            return sub
    available = [s["merchant"] for s in report["subscriptions"]]
    return {"error": f"No subscription found matching '{merchant}'.", "available_merchants": available}


def get_savings_summary(report: Report) -> dict:
    """Return the aggregate summary: total subscriptions, total monthly/
    annual cost, cost broken down by category, and how much of the annual
    cost is attributable to price increases."""
    return report["summary"]


def get_top_subscriptions_by_cost(report: Report, limit: int = 3) -> list[dict]:
    """Return the `limit` most expensive subscriptions by annual cost."""
    ranked = sorted(report["subscriptions"], key=lambda s: s["estimated_annual_cost"], reverse=True)
    return ranked[:limit]


def get_subscriptions_with_price_increases(report: Report) -> list[dict]:
    """Return only subscriptions that had a detected price increase, each
    with its price_change_events history."""
    return [s for s in report["subscriptions"] if s["price_increased"]]


# Registry used by assistant.py to dispatch tool calls by name, and to build
# the JSON schema list sent to the model.
TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "list_subscriptions": list_subscriptions,
    "get_subscription_detail": get_subscription_detail,
    "get_savings_summary": get_savings_summary,
    "get_top_subscriptions_by_cost": get_top_subscriptions_by_cost,
    "get_subscriptions_with_price_increases": get_subscriptions_with_price_increases,
}

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_subscriptions",
            "description": list_subscriptions.__doc__.strip(),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_subscription_detail",
            "description": get_subscription_detail.__doc__.strip(),
            "parameters": {
                "type": "object",
                "properties": {"merchant": {"type": "string", "description": "Merchant name to look up"}},
                "required": ["merchant"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_savings_summary",
            "description": get_savings_summary.__doc__.strip(),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_subscriptions_by_cost",
            "description": get_top_subscriptions_by_cost.__doc__.strip(),
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "How many to return, default 3"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_subscriptions_with_price_increases",
            "description": get_subscriptions_with_price_increases.__doc__.strip(),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
