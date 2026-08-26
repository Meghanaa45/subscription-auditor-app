#!/usr/bin/env python3
"""Generate a realistic synthetic bank transaction CSV with known recurring
subscriptions injected (messy descriptor variants, date jitter, a mid-series
price increase) alongside non-subscription noise (one-off purchases, and a
"habit" merchant with irregular timing that should NOT be flagged).

Ground truth is derived by running the actual normalization pipeline against
the generated data, so the labels are guaranteed to be consistent with
whatever canonical merchant names the pipeline produces.

Usage:
    python scripts/generate_synthetic_data.py --months 14 --seed 42 \
        --out-transactions data/sample_transactions.csv \
        --out-ground-truth data/ground_truth.csv
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.normalize import normalize_merchants  # noqa: E402

# (canonical_id, descriptor_variants, monthly_amount, day_of_month, price_increase_month)
SUBSCRIPTIONS = [
    ("netflix", ["NETFLIX.COM", "NETFLIX  LOS GATOS CA", "NFLX*STREAMING"], 15.49, 3, 8),
    ("spotify", ["SPOTIFY USA", "SPOTIFY*PREMIUM", "SPOTIFY.COM"], 10.99, 12, None),
    ("adobe", ["ADOBE  CREATIVE CLOUD", "ADOBE SYSTEMS INC", "ADOBE   SAN JOSE CA"], 54.99, 21, 9),
    ("nyt", ["NYTIMES SUBSCRIPTION", "NYT DIGITAL", "NEW YORK TIMES"], 17.00, 5, None),
    ("chatgpt", ["OPENAI CHATGPT SUBSCR", "OPENAI *CHATGPT", "CHATGPT SUBSCRIPTION"], 20.00, 17, None),
    ("planet_fitness", ["PLANET FITNESS #4521", "PLANET FITNESS  CHICAGO IL", "PLANETFITNESS.COM"], 24.99, 1, None),
]

# A merchant with weekly-ish real habit spending that must NOT be classified
# as a subscription: amounts and gaps are both irregular by design.
HABIT_MERCHANT_VARIANTS = ["BLUE BOTTLE COFFEE #12", "BLUE BOTTLE COFFEE SF", "BLUEBOTTLE   MARKET ST"]

ONE_OFF_MERCHANTS = [
    "BEST BUY #331",
    "TARGET T-2210",
    "UNITED AIRLINES",
    "HOME DEPOT #0473",
    "IKEA SF EMERYVILLE",
    "AMAZON.COM RETAIL",
    "SHELL OIL 57402910",
    "TRADER JOE S #142",
    "WHOLE FOODS MKT",
    "UBER TRIP HELP.UBER.COM",
]


def _daterange_months(start: date, months: int) -> list[date]:
    return [start + timedelta(days=30 * i) for i in range(months)]


def generate(months: int, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    start = date.today() - timedelta(days=30 * months)
    rows = []

    for sub_id, variants, base_amount, day_of_month, increase_month in SUBSCRIPTIONS:
        for i in range(months):
            month_date = start + timedelta(days=30 * i)
            jitter = rng.randint(-2, 2)
            charge_date = date(month_date.year, month_date.month, min(day_of_month, 28)) + timedelta(days=jitter)
            amount = base_amount
            if increase_month is not None and i >= increase_month:
                amount = round(base_amount * 1.15, 2)
            descriptor = rng.choice(variants)
            rows.append(
                {
                    "date": charge_date,
                    "description": descriptor,
                    "amount": round(amount + rng.uniform(-0.0, 0.0), 2),
                    "true_group": sub_id,
                    "true_is_subscription": True,
                }
            )

    # Habit merchant: frequent but irregular gaps (5-12 days) and irregular
    # amounts ($4-$9) - looks recurring at a glance but should fail the
    # detector's interval/amount-consistency checks.
    cursor = start
    end = start + timedelta(days=30 * months)
    while cursor < end:
        cursor += timedelta(days=rng.randint(5, 12))
        rows.append(
            {
                "date": cursor,
                "description": rng.choice(HABIT_MERCHANT_VARIANTS),
                "amount": round(rng.uniform(4.25, 8.75), 2),
                "true_group": "blue_bottle_habit",
                "true_is_subscription": False,
            }
        )

    # One-off purchases scattered across the period, random merchants,
    # random amounts, never repeating on a schedule.
    num_one_offs = months * 6
    for _ in range(num_one_offs):
        offset = rng.randint(0, 30 * months - 1)
        rows.append(
            {
                "date": start + timedelta(days=offset),
                "description": rng.choice(ONE_OFF_MERCHANTS),
                "amount": round(rng.uniform(8.0, 220.0), 2),
                "true_group": "one_off",
                "true_is_subscription": False,
            }
        )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def derive_ground_truth(df: pd.DataFrame) -> pd.DataFrame:
    """Run the real normalization pipeline on the generated data and label
    each resulting canonical merchant as a subscription if the majority of
    its underlying transactions were generated as subscription charges."""
    normalized = normalize_merchants(df[["date", "description", "amount"]].copy())
    normalized["true_is_subscription"] = df["true_is_subscription"].values

    grouped = normalized.groupby("merchant")["true_is_subscription"].mean()
    ground_truth = grouped.reset_index()
    ground_truth["is_subscription"] = ground_truth["true_is_subscription"] >= 0.5
    return ground_truth[["merchant", "is_subscription"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=14)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-transactions", default="data/sample_transactions.csv")
    parser.add_argument("--out-ground-truth", default="data/ground_truth.csv")
    args = parser.parse_args()

    df = generate(args.months, args.seed)
    ground_truth = derive_ground_truth(df)

    out_tx_path = Path(args.out_transactions)
    out_gt_path = Path(args.out_ground_truth)
    out_tx_path.parent.mkdir(parents=True, exist_ok=True)
    out_gt_path.parent.mkdir(parents=True, exist_ok=True)

    public_columns = df[["date", "description", "amount"]].copy()
    public_columns["date"] = public_columns["date"].dt.strftime("%Y-%m-%d")
    public_columns.to_csv(out_tx_path, index=False)
    ground_truth.to_csv(out_gt_path, index=False)

    print(f"Wrote {len(public_columns)} transactions to {out_tx_path}")
    print(f"Wrote {len(ground_truth)} ground-truth merchant labels to {out_gt_path}")


if __name__ == "__main__":
    main()
