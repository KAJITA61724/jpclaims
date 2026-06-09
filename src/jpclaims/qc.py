"""Quality control reporting."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from jpclaims.config import definition_hash


def generate_qc_report(
    input_tables: dict[str, pd.DataFrame | None],
    output: pd.DataFrame,
    code_definitions: dict[str, Any] | None = None,
    definition_hit_counts: dict[str, int] | None = None,
    cooccurrence_hit_counts: dict[str, int] | None = None,
    library_version: str = "0.1.0",
) -> dict[str, Any]:
    defs = code_definitions or {}
    input_counts = {
        name: int(len(df)) if df is not None else 0 for name, df in input_tables.items()
    }
    input_patients = {
        name: int(df["person_id"].nunique()) if df is not None and "person_id" in df.columns else 0
        for name, df in input_tables.items()
    }
    person = input_tables.get("person")
    retention = None
    duplicate_patients = 0
    if person is not None:
        duplicate_patients = int(output["person_id"].duplicated().sum())
        retention = float(len(output) / max(len(person), 1))

    missing_rate = {
        col: float(output[col].isna().mean()) for col in output.columns if output[col].isna().any()
    }
    flag_cols = [c for c in output.columns if c.endswith("_flag") or c.endswith("_flag_obs")]
    flag_positive_rate = {
        col: float(output[col].mean()) for col in flag_cols if col in output.columns
    }
    count_cols = [c for c in output.columns if "_count_" in c or c.endswith("_count")]
    count_distribution = {
        col: {
            "min": float(output[col].min()) if col in output.columns else 0,
            "max": float(output[col].max()) if col in output.columns else 0,
            "mean": float(output[col].mean()) if col in output.columns else 0,
        }
        for col in count_cols[:20]
    }
    ym_cols = [c for c in output.columns if c.endswith("_ym") or c.endswith("_ym_obs")]
    first_last_month_range = {}
    for col in ym_cols[:10]:
        vals = pd.to_numeric(output[col], errors="coerce").dropna()
        if not vals.empty:
            first_last_month_range[col] = {"min": int(vals.min()), "max": int(vals.max())}

    suspected_rate = None
    if "dx" in "".join(output.columns):
        suspected_cols = [c for c in output.columns if c.endswith("_suspected_count")]
        confirmed_cols = [c for c in output.columns if c.endswith("_confirmed_count")]
        if suspected_cols and confirmed_cols:
            s = output[suspected_cols].sum().sum()
            c = output[confirmed_cols].sum().sum()
            suspected_rate = float(s / max(s + c, 1))

    report = {
        "input_table_row_counts": input_counts,
        "input_table_unique_patient_counts": input_patients,
        "output_row_count": int(len(output)),
        "output_unique_patient_count": int(output["person_id"].nunique()),
        "patient_retention_check": retention,
        "duplicate_patient_id_count": duplicate_patients,
        "missing_rate_by_column": missing_rate,
        "flag_positive_rate": flag_positive_rate,
        "count_distribution": count_distribution,
        "first_last_month_range": first_last_month_range,
        "unmapped_code_rate": None,
        "invalid_code_rate": None,
        "suspected_diagnosis_rate": suspected_rate,
        "primary_diagnosis_rate": None,
        "definition_hit_counts": definition_hit_counts or {},
        "cooccurrence_hit_counts": cooccurrence_hit_counts or {},
        "window_availability_counts": _window_availability_counts(output),
        "washout_case_counts": _washout_case_counts(output),
        "code_definition_hash": defs.get("_definition_hash") or definition_hash(defs),
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "library_version": library_version,
    }
    return report


def _window_availability_counts(df: pd.DataFrame) -> dict[str, int]:
    cols = [c for c in df.columns if c.endswith("_available_flag")]
    return {col: int(df[col].sum()) for col in cols if col in df.columns}


def _washout_case_counts(df: pd.DataFrame) -> dict[str, int]:
    cols = [c for c in df.columns if "_incident_" in c and c.endswith("_flag")]
    return {col: int(df[col].sum()) for col in cols if col in df.columns}
