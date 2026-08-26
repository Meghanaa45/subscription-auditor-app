import pandas as pd
import pytest

from app.core.ingest import AmbiguousFormatError, UnrecognizedFormatError, load_transactions, load_transactions_multi


def _write_csv(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)
    return path


def test_loads_generic_format(tmp_path):
    path = _write_csv(
        tmp_path,
        "generic.csv",
        "date,description,amount\n2024-01-01,NETFLIX.COM,15.49\n2024-02-01,SPOTIFY.COM,10.99\n",
    )
    df = load_transactions(path)
    assert len(df) == 2
    assert list(df.columns) == ["date", "description", "amount", "account"]
    assert df["amount"].tolist() == [15.49, 10.99]


def test_chase_format_flips_negative_charges_positive(tmp_path):
    path = _write_csv(
        tmp_path,
        "chase.csv",
        "Transaction Date,Description,Amount\n01/15/2024,NETFLIX.COM,-15.49\n",
    )
    df = load_transactions(path)
    assert df["amount"].iloc[0] == 15.49


def test_amex_format_requires_explicit_bank_when_ambiguous(tmp_path):
    # Amex and Bank of America both use plain Date/Description/Amount
    # headers but different sign conventions, so auto-detection can't
    # safely guess - this must be disambiguated explicitly.
    path = _write_csv(
        tmp_path,
        "amex.csv",
        "Date,Description,Amount\n01/15/2024,NETFLIX.COM,15.49\n",
    )
    with pytest.raises(AmbiguousFormatError):
        load_transactions(path)

    df = load_transactions(path, bank="amex")
    assert df["amount"].iloc[0] == 15.49

    df_as_bofa = load_transactions(path, bank="bank_of_america")
    # Misapplying the wrong profile flips the sign, turning a real charge
    # into a "credit" that gets filtered out - which is exactly why
    # ambiguous formats must be disambiguated rather than guessed.
    assert df_as_bofa.empty


def test_refunds_are_dropped(tmp_path):
    path = _write_csv(
        tmp_path,
        "generic.csv",
        "date,description,amount\n2024-01-01,NETFLIX.COM,15.49\n2024-01-05,REFUND,-15.49\n",
    )
    df = load_transactions(path)
    assert len(df) == 1
    assert df["description"].iloc[0] == "NETFLIX.COM"


def test_unrecognized_format_raises(tmp_path):
    path = _write_csv(tmp_path, "weird.csv", "foo,bar,baz\n1,2,3\n")
    with pytest.raises(UnrecognizedFormatError):
        load_transactions(path)


def test_load_transactions_multi_concatenates_and_sorts(tmp_path):
    path_a = _write_csv(
        tmp_path, "a.csv", "date,description,amount\n2024-02-01,SPOTIFY.COM,10.99\n"
    )
    path_b = _write_csv(
        tmp_path, "b.csv", "date,description,amount\n2024-01-01,NETFLIX.COM,15.49\n"
    )
    df = load_transactions_multi([path_a, path_b])
    assert len(df) == 2
    assert df["date"].tolist() == sorted(df["date"].tolist())
    assert df["date"].iloc[0] == pd.Timestamp("2024-01-01")
