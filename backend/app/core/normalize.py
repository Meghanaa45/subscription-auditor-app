"""Normalize raw bank-statement merchant descriptors into canonical merchant
names so that recurring charges from the same real-world merchant group
together, even when the raw text varies transaction to transaction
(e.g. "NETFLIX.COM", "NETFLIX  LOS GATOS CA", "NFLX*STREAMING").

Two-stage approach:
  1. Known-merchant lookup (merchant_lookup.py) for common recurring billers.
  2. For anything unmatched: strip processor/location noise, then fuzzy-cluster
     remaining descriptors that are near-duplicates of each other.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

import pandas as pd

from app.core.merchant_lookup import lookup_known_merchant

# Common noise patterns found in card processor descriptors.
_STORE_NUMBER_RE = re.compile(r"#\d+")
_TRAILING_DIGITS_RE = re.compile(r"\b\d{4,}\b")
_STATE_CODE_RE = re.compile(r"\b[A-Z]{2}\b$")
_PROCESSOR_PREFIX_RE = re.compile(r"^(SQ|TST|PY|IVP|CKO|PP)\s*\*\s*", re.IGNORECASE)
_SEPARATOR_RE = re.compile(r"[*#/]+")
_MULTI_SPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^A-Za-z0-9 ]")

FUZZY_MATCH_THRESHOLD = 0.82


def clean_descriptor(raw: str) -> str:
    """Strip processor prefixes, store numbers, trailing digit strings,
    trailing state codes, and punctuation noise from a raw descriptor,
    returning an uppercased, whitespace-normalized string."""
    text = raw.strip()
    text = _PROCESSOR_PREFIX_RE.sub("", text)
    text = _SEPARATOR_RE.sub(" ", text)
    text = _STORE_NUMBER_RE.sub("", text)
    text = _STATE_CODE_RE.sub("", text)
    text = _TRAILING_DIGITS_RE.sub("", text)
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text.upper()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _fuzzy_cluster(cleaned_names: list[str]) -> dict[str, str]:
    """Greedily cluster near-duplicate cleaned descriptors and map each
    original cleaned name to a representative canonical label (the most
    frequent member's name, chosen deterministically as the shortest
    alphabetically-first string in the cluster for stability)."""
    unique_names = sorted(set(cleaned_names))
    clusters: list[list[str]] = []

    for name in unique_names:
        placed = False
        for cluster in clusters:
            if any(_similarity(name, member) >= FUZZY_MATCH_THRESHOLD for member in cluster):
                cluster.append(name)
                placed = True
                break
        if not placed:
            clusters.append([name])

    mapping: dict[str, str] = {}
    for cluster in clusters:
        representative = min(cluster, key=lambda s: (len(s), s))
        for member in cluster:
            mapping[member] = representative.title()
    return mapping


def normalize_merchants(transactions: pd.DataFrame) -> pd.DataFrame:
    """Add `merchant` (canonical name) and `category` columns to a
    transactions DataFrame that has a `description` column."""
    df = transactions.copy()

    known_matches = df["description"].apply(lookup_known_merchant)
    df["merchant"] = known_matches.apply(lambda m: m[0] if m else None)
    df["category"] = known_matches.apply(lambda m: m[1] if m else None)

    unmatched_mask = df["merchant"].isna()
    if unmatched_mask.any():
        cleaned = df.loc[unmatched_mask, "description"].apply(clean_descriptor)
        cluster_map = _fuzzy_cluster(cleaned.tolist())
        df.loc[unmatched_mask, "merchant"] = cleaned.map(cluster_map)
        df.loc[unmatched_mask, "category"] = "uncategorized"

    return df
