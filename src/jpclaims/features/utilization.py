"""Healthcare utilization features."""

from __future__ import annotations

import pandas as pd


def build_utilization_features(
    person: pd.DataFrame,
    claim: pd.DataFrame | None,
    visit_event: pd.DataFrame | None = None,
) -> pd.DataFrame:
    out = person[["person_id"]].copy()
    source = claim if claim is not None else visit_event
    if source is None or source.empty:
        out["visit_months"] = 0
        out["outpatient_visit_count"] = 0
        out["inpatient_flag"] = 0
        out["inpatient_count"] = 0
        out["facility_count"] = 0
        out["department_count"] = 0
        return out
    month_col = "claim_month" if "claim_month" in source.columns else "event_month"
    agg = (
        source.groupby("person_id")
        .agg(
            visit_months=(month_col, "nunique"),
            outpatient_visit_count=("claim_id" if "claim_id" in source.columns else month_col, "nunique"),
            facility_count=("facility_id", "nunique") if "facility_id" in source.columns else (month_col, "nunique"),
            department_count=("department", "nunique") if "department" in source.columns else (month_col, "nunique"),
        )
        .reset_index()
    )
    if "claim_type" in source.columns:
        inpatient = source.loc[source["claim_type"].astype(str).isin(["入院", "DPC"])]
        in_agg = (
            inpatient.groupby("person_id")
            .agg(
                inpatient_flag=(month_col, "size"),
                inpatient_count=("claim_id" if "claim_id" in inpatient.columns else month_col, "nunique"),
            )
            .reset_index()
        )
        in_agg["inpatient_flag"] = (in_agg["inpatient_flag"] > 0).astype(int)
        agg = agg.merge(in_agg, on="person_id", how="left")
    else:
        agg["inpatient_flag"] = 0
        agg["inpatient_count"] = 0
    out = out.merge(agg, on="person_id", how="left")
    fill_zero = [c for c in out.columns if c != "person_id"]
    out[fill_zero] = out[fill_zero].fillna(0)
    for col in ["visit_months", "outpatient_visit_count", "inpatient_flag", "inpatient_count", "facility_count", "department_count"]:
        if col in out.columns:
            out[col] = out[col].astype(int)
    return out
