"""Optional CLI entry point for running an audit without the API/frontend.
Usage: python -m app.cli data/sample_transactions.csv --evaluate data/ground_truth.csv
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from app.core.detector import detect_subscriptions
from app.core.evaluate import evaluate_detections
from app.core.ingest import load_transactions_multi
from app.core.normalize import normalize_merchants
from app.core.report import render_console_table, write_json_report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_paths", nargs="+", help="One or more bank statement CSV exports")
    parser.add_argument(
        "--bank",
        default=None,
        choices=["chase", "bank_of_america", "amex", "discover", "generic"],
        help="Force a specific bank CSV format instead of auto-detecting",
    )
    parser.add_argument("--json-out", default=None, help="Write the full report as JSON to this path")
    parser.add_argument("--evaluate", default=None, metavar="GROUND_TRUTH_CSV")
    args = parser.parse_args(argv)

    transactions = load_transactions_multi(args.csv_paths, bank=args.bank)
    if transactions.empty:
        print("No usable transactions found in the provided file(s).")
        sys.exit(1)

    normalized = normalize_merchants(transactions)
    matches = detect_subscriptions(normalized)
    print(render_console_table(matches))

    if args.json_out:
        write_json_report(matches, args.json_out)
        print(f"\nFull report written to {args.json_out}")

    if args.evaluate:
        ground_truth = pd.read_csv(args.evaluate)
        result = evaluate_detections(matches, ground_truth)
        print("\n--- Evaluation against ground truth ---")
        print(f"Precision: {result.precision:.3f}  Recall: {result.recall:.3f}  F1: {result.f1:.3f}")
        if result.false_positives:
            print(f"False positives: {result.false_positives}")
        if result.false_negatives:
            print(f"False negatives: {result.false_negatives}")


if __name__ == "__main__":
    main()
