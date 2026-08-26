"""Load transaction CSV exports from different bank formats into a single
canonical schema: date (datetime64), description (str), amount (float, positive
for a charge), account (str).

Each bank exports slightly different column names, date formats, and sign
conventions for amounts (some list charges as negative, some as positive).
Rather than guessing, we match the incoming header against known bank
profiles and fall back to a generic profile if none match.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class BankProfile:
    name: str
    date_column: str
    description_column: str
    amount_column: str
    date_format: str | None
    # If True, charges are stored as negative numbers (typical for many
    # checking-account exports) and need to be flipped to positive.
    charges_are_negative: bool


BANK_PROFILES: list[BankProfile] = [
    BankProfile(
        name="chase",
        date_column="Transaction Date",
        description_column="Description",
        amount_column="Amount",
        date_format="%m/%d/%Y",
        charges_are_negative=True,
    ),
    BankProfile(
        name="bank_of_america",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        date_format="%m/%d/%Y",
        charges_are_negative=True,
    ),
    BankProfile(
        name="amex",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        date_format="%m/%d/%Y",
        charges_are_negative=False,
    ),
    BankProfile(
        name="discover",
        date_column="Trans. Date",
        description_column="Description",
        amount_column="Amount",
        date_format="%m/%d/%Y",
        charges_are_negative=False,
    ),
    BankProfile(
        name="generic",
        date_column="date",
        description_column="description",
        amount_column="amount",
        date_format=None,
        charges_are_negative=False,
    ),
]


class UnrecognizedFormatError(ValueError):
    """Raised when a CSV's header doesn't match any known bank profile."""


class AmbiguousFormatError(ValueError):
    """Raised when a CSV's header matches more than one bank profile with
    identical column names but different sign conventions (e.g. Bank of
    America and Amex both export Date/Description/Amount, but one records
    charges as negative and the other as positive). Auto-detection can't
    safely guess in this case; the caller must pass `bank=` explicitly."""


def _profile_by_name(name: str) -> BankProfile:
    for profile in BANK_PROFILES:
        if profile.name == name:
            return profile
    known = [p.name for p in BANK_PROFILES]
    raise ValueError(f"Unknown bank profile '{name}'. Known profiles: {known}")


def _match_profile(columns: list[str]) -> BankProfile:
    """Match CSV columns to a bank profile. Named bank profiles (Chase, BofA,
    etc.) are matched with exact case first. If more than one non-generic
    profile matches identical column names (which happens in practice, since
    several banks export plain "Date, Description, Amount" headers despite
    using different sign conventions), detection is ambiguous and the caller
    must disambiguate with the `bank=` argument. The `generic` profile is
    tried last and matches case-insensitively.
    """
    column_set_exact = set(columns)
    candidates = []
    for profile in BANK_PROFILES:
        if profile.name == "generic":
            continue
        required_exact = {profile.date_column, profile.description_column, profile.amount_column}
        if required_exact.issubset(column_set_exact):
            candidates.append(profile)

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        names = [c.name for c in candidates]
        raise AmbiguousFormatError(
            f"CSV columns {columns} match multiple bank formats ({names}) with the same "
            "header but potentially different sign conventions. Pass bank=<name> explicitly, "
            f"e.g. bank='{names[0]}'."
        )

    normalized = {c.strip().lower() for c in columns}
    generic = next(p for p in BANK_PROFILES if p.name == "generic")
    required_generic = {generic.date_column.lower(), generic.description_column.lower(), generic.amount_column.lower()}
    if required_generic.issubset(normalized):
        return generic

    raise UnrecognizedFormatError(
        f"Could not match CSV columns {columns} to a known bank format. "
        f"Expected one of: {[p.name for p in BANK_PROFILES]}. "
        "Use the 'generic' format with columns: date, description, amount."
    )


def load_transactions(csv_path: str | Path, account_label: str | None = None, bank: str | None = None) -> pd.DataFrame:
    """Load a bank CSV export into the canonical transaction schema.

    `bank` optionally names a profile explicitly (see BANK_PROFILES) to skip
    auto-detection, which is required when a CSV's headers are ambiguous
    between two profiles (see AmbiguousFormatError).

    Returns a DataFrame with columns: date, description, amount, account.
    `amount` is always positive for a charge/purchase; refunds/credits (if
    present) come through as negative and are dropped, since they are not
    relevant to recurring-charge detection.
    """
    csv_path = Path(csv_path)
    raw = pd.read_csv(csv_path)
    raw.columns = [c.strip() for c in raw.columns]

    profile = _profile_by_name(bank) if bank else _match_profile(list(raw.columns))
    # Column matching is case-insensitive, but the actual DataFrame columns
    # may differ in case from the profile's declared names, so resolve the
    # real column names before indexing into `raw`.
    column_by_lower = {c.lower(): c for c in raw.columns}
    date_col = column_by_lower[profile.date_column.lower()]
    description_col = column_by_lower[profile.description_column.lower()]
    amount_col = column_by_lower[profile.amount_column.lower()]

    df = pd.DataFrame()
    df["date"] = pd.to_datetime(raw[date_col], format=profile.date_format, errors="coerce")
    df["description"] = raw[description_col].astype(str).str.strip()
    df["amount"] = pd.to_numeric(raw[amount_col], errors="coerce")

    if profile.charges_are_negative:
        df["amount"] = -df["amount"]

    df["account"] = account_label or csv_path.stem

    before = len(df)
    df = df.dropna(subset=["date", "description", "amount"])
    dropped = before - len(df)

    # Only charges are relevant to subscription detection, not refunds/payments.
    df = df[df["amount"] > 0].reset_index(drop=True)

    if dropped:
        import logging

        logging.getLogger(__name__).warning(
            "Dropped %d rows with missing/unparseable date, description, or amount from %s",
            dropped,
            csv_path,
        )

    return df.sort_values("date").reset_index(drop=True)


def load_transactions_multi(csv_paths: list[str | Path], bank: str | None = None) -> pd.DataFrame:
    """Load and concatenate multiple bank CSV exports into one DataFrame.
    `bank`, if given, is applied to every file (use `load_transactions`
    directly if different files need different profiles)."""
    frames = [load_transactions(path, bank=bank) for path in csv_paths]
    if not frames:
        return pd.DataFrame(columns=["date", "description", "amount", "account"])
    return pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
