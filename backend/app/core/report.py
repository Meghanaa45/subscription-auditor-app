"""Render detected subscriptions as a console table and/or a JSON report."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.detector import SubscriptionMatch
from app.core.pricing import price_change_events, savings_summary


def build_report_dict(matches: list[SubscriptionMatch]) -> dict:
    summary = savings_summary(matches)
    subscriptions = []
    for m in matches:
        events = price_change_events(m)
        subscriptions.append(
            {
                "merchant": m.merchant,
                "category": m.category,
                "billing_period": m.period,
                "occurrences_detected": m.occurrences,
                "first_charge_date": m.first_date.strftime("%Y-%m-%d"),
                "last_charge_date": m.last_date.strftime("%Y-%m-%d"),
                "current_amount": m.last_amount,
                "estimated_monthly_cost": m.monthly_cost,
                "estimated_annual_cost": m.annual_cost,
                "confidence": m.confidence,
                "price_increased": m.price_increased,
                "price_change_events": [
                    {
                        "date": e.date.strftime("%Y-%m-%d"),
                        "old_amount": e.old_amount,
                        "new_amount": e.new_amount,
                        "pct_change": e.pct_change,
                    }
                    for e in events
                ],
            }
        )
    return {"summary": summary, "subscriptions": subscriptions}


def write_json_report(matches: list[SubscriptionMatch], output_path: str | Path) -> None:
    report = build_report_dict(matches)
    Path(output_path).write_text(json.dumps(report, indent=2))


def render_console_table(matches: list[SubscriptionMatch]) -> str:
    if not matches:
        return "No recurring subscriptions detected."

    headers = ["Merchant", "Category", "Period", "Current $", "Monthly $", "Annual $", "Conf.", "Price ^"]
    rows = [
        [
            m.merchant,
            m.category,
            m.period,
            f"{m.last_amount:.2f}",
            f"{m.monthly_cost:.2f}",
            f"{m.annual_cost:.2f}",
            f"{m.confidence:.2f}",
            "yes" if m.price_increased else "",
        ]
        for m in matches
    ]

    widths = [max(len(str(x)) for x in [h, *[r[i] for r in rows]]) for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    separator = "-" * len(line)
    body = "\n".join("  ".join(str(cell).ljust(w) for cell, w in zip(row, widths)) for row in rows)

    summary = savings_summary(matches)
    footer = (
        f"\n{separator}\n"
        f"Detected {summary['total_subscriptions']} subscriptions | "
        f"${summary['total_monthly_cost']:.2f}/mo | ${summary['total_annual_cost']:.2f}/yr\n"
        f"{summary['subscriptions_with_price_increases']} had price increases, "
        f"adding ${summary['annual_cost_added_by_price_increases']:.2f}/yr"
    )
    return f"{line}\n{separator}\n{body}{footer}"
