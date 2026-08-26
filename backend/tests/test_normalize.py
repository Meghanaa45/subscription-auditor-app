import pandas as pd

from app.core.normalize import clean_descriptor, normalize_merchants


def test_clean_descriptor_strips_processor_prefix():
    assert clean_descriptor("SQ *BLUE BOTTLE COFFEE") == "BLUE BOTTLE COFFEE"


def test_clean_descriptor_strips_store_numbers():
    assert clean_descriptor("PLANET FITNESS #4521") == "PLANET FITNESS"


def test_clean_descriptor_strips_trailing_state_code():
    assert clean_descriptor("BLUE BOTTLE COFFEE SF").startswith("BLUE BOTTLE COFFEE")


def test_known_merchant_variants_collapse_to_same_canonical_name():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "description": ["NETFLIX.COM", "NETFLIX  LOS GATOS CA", "NFLX*STREAMING"],
            "amount": [15.49, 15.49, 15.49],
        }
    )
    result = normalize_merchants(df)
    assert result["merchant"].nunique() == 1
    assert result["merchant"].iloc[0] == "Netflix"
    assert result["category"].iloc[0] == "streaming"


def test_unknown_merchant_variants_fuzzy_cluster_together():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "description": ["ANYTIME FITNESS #331", "ANYTIME FITNESS #892"],
            "amount": [29.99, 29.99],
        }
    )
    result = normalize_merchants(df)
    assert result["merchant"].nunique() == 1


def test_distinct_merchants_do_not_collapse():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "description": ["TARGET T-2210", "WHOLE FOODS MARKET"],
            "amount": [45.00, 62.00],
        }
    )
    result = normalize_merchants(df)
    assert result["merchant"].nunique() == 2
