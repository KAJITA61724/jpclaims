"""Schema and data quality validation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.dates import validate_ym_format, ym_to_int
from jpclaims.exceptions import SchemaValidationError
from jpclaims.io import preserve_string_codes
from jpclaims.schema import TABLE_REQUIRED_COLUMNS


def validate_required_columns(df: pd.DataFrame, table: str) -> None:
    required = TABLE_REQUIRED_COLUMNS.get(table, [])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SchemaValidationError(f"{table}: missing required columns: {missing}")


def validate_person(df: pd.DataFrame) -> dict[str, Any]:
    validate_required_columns(df, "person")
    issues: dict[str, Any] = {}
    if df["person_id"].isna().any():
        issues["missing_person_id"] = int(df["person_id"].isna().sum())
    try:
        validate_ym_format(df["observation_start_ym"], "observation_start_ym")
        validate_ym_format(df["observation_end_ym"], "observation_end_ym")
    except ValueError as exc:
        issues["invalid_ym"] = str(exc)
    obs_start = ym_to_int(df["observation_start_ym"])
    obs_end = ym_to_int(df["observation_end_ym"])
    invalid_obs = obs_start > obs_end
    if invalid_obs.any():
        issues["observation_start_after_end"] = int(invalid_obs.sum())
    if "sex" in df.columns:
        valid_sex = df["sex"].isin([1, 2, "1", "2", 1.0, 2.0]) | df["sex"].isna()
        if not valid_sex.all():
            issues["invalid_sex"] = int((~valid_sex).sum())
    return issues


def validate_claims(df: pd.DataFrame) -> dict[str, Any]:
    validate_required_columns(df, "claim")
    issues: dict[str, Any] = {}
    if df["claim_id"].isna().any():
        issues["missing_claim_id"] = int(df["claim_id"].isna().sum())
    if df["person_id"].isna().any():
        issues["missing_person_id"] = int(df["person_id"].isna().sum())
    numeric_cols = ["total_points", "total_visit_days"]
    for col in numeric_cols:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            if (vals < 0).any():
                issues[f"negative_{col}"] = int((vals < 0).sum())
    return issues


def validate_table(df: pd.DataFrame | None, table: str) -> dict[str, Any]:
    if df is None or df.empty:
        return {}
    df = preserve_string_codes(df, table)
    if table == "person":
        return validate_person(df)
    if table == "claim":
        return validate_claims(df)
    validate_required_columns(df, table)
    return {}


def validate_events(events: dict[str, pd.DataFrame | None]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for table, df in events.items():
        if df is not None and not df.empty:
            report[table] = validate_table(df, table)
    return report
