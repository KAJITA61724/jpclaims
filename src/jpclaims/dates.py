"""Year-month utilities."""

from __future__ import annotations

import pandas as pd


def ym_to_int(ym: pd.Series) -> pd.Series:
    """Convert YYYYMM values to nullable integer series."""
    return pd.to_numeric(ym, errors="coerce").astype("Int64")


def ym_to_month_index(ym: pd.Series) -> pd.Series:
    """Convert YYYYMM to absolute month index (year*12 + month)."""
    values = pd.to_numeric(ym, errors="coerce")
    year = values // 100
    month = values % 100
    return year * 12 + month


def month_index_to_ym(index: int) -> int:
    year = index // 12
    month = index % 12
    if month == 0:
        year -= 1
        month = 12
    return int(year * 100 + month)


def months_between(start_ym: pd.Series, end_ym: pd.Series) -> pd.Series:
    """Inclusive month span between two YYYYMM series."""
    start = ym_to_month_index(start_ym)
    end = ym_to_month_index(end_ym)
    return (end - start + 1).clip(lower=0)


def months_diff(start_ym: pd.Series, end_ym: pd.Series) -> pd.Series:
    """Month difference end - start (non-inclusive span)."""
    return ym_to_month_index(end_ym) - ym_to_month_index(start_ym)


def add_months(ym: pd.Series, n: int) -> pd.Series:
    idx = ym_to_month_index(ym) + n
    return idx.map(month_index_to_ym).astype("Int64")


def validate_ym_format(ym: pd.Series, name: str = "ym") -> None:
    values = pd.to_numeric(ym, errors="coerce")
    invalid = values.isna() | (values % 100 < 1) | (values % 100 > 12) | (values // 100 < 1900)
    if invalid.any():
        n = int(invalid.sum())
        raise ValueError(f"{name}: {n} invalid YYYYMM values")
