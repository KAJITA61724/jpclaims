"""I/O utilities for claims tables."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from jpclaims.schema import STRING_CODE_COLUMNS


def read_claims(
    path: str | Path,
    *,
    format: Literal["csv", "parquet", "auto"] = "auto",
    dtype: dict | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Read a claims table from CSV or Parquet."""
    p = Path(path)
    if format == "auto":
        suffix = p.suffix.lower()
        if suffix == ".parquet":
            format = "parquet"
        elif suffix in {".csv", ".gz", ".txt"}:
            format = "csv"
        else:
            raise ValueError(f"Cannot infer format for {p}")

    if format == "parquet":
        df = pd.read_parquet(p, **kwargs)
    else:
        df = pd.read_csv(p, **kwargs)

    if dtype:
        for col, dt in dtype.items():
            if col in df.columns:
                df[col] = df[col].astype(dt)
    return df


def write_table(df: pd.DataFrame, path: str | Path, *, format: str = "auto") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if format == "auto":
        format = "parquet" if p.suffix.lower() == ".parquet" else "csv"
    if format == "parquet":
        df.to_parquet(p, index=False)
    else:
        df.to_csv(p, index=False)


def preserve_string_codes(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Ensure code columns remain strings with leading zeros preserved."""
    out = df.copy()
    for col in STRING_CODE_COLUMNS.get(table, []):
        if col in out.columns:
            out[col] = out[col].astype(str).replace({"nan": pd.NA, "<NA>": pd.NA, "None": pd.NA})
    return out
