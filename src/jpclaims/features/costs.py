"""Cost and points features."""

from __future__ import annotations

import pandas as pd


def build_cost_features(
    person: pd.DataFrame,
    claim: pd.DataFrame | None,
    drug_event: pd.DataFrame | None = None,
    yen_per_point: float = 10.0,
) -> pd.DataFrame:
    out = person[["person_id"]].copy()
    if claim is None or claim.empty:
        out["total_points"] = 0
        out["estimated_cost_yen"] = 0.0
        out["inpatient_points"] = 0
        out["outpatient_points"] = 0
        return out
    claim = claim.copy()
    claim["total_points"] = pd.to_numeric(claim.get("total_points", 0), errors="coerce").fillna(0)
    agg = claim.groupby("person_id").agg(total_points=("total_points", "sum")).reset_index()
    if "claim_type" in claim.columns:
        inpatient = claim.loc[claim["claim_type"].astype(str).isin(["入院", "DPC"])]
        outpatient = claim.loc[~claim["claim_type"].astype(str).isin(["入院", "DPC"])]
        in_pts = inpatient.groupby("person_id")["total_points"].sum().rename("inpatient_points")
        out_pts = outpatient.groupby("person_id")["total_points"].sum().rename("outpatient_points")
        agg = agg.merge(in_pts, on="person_id", how="left").merge(out_pts, on="person_id", how="left")
    else:
        agg["inpatient_points"] = 0
        agg["outpatient_points"] = agg["total_points"]
    agg = agg.fillna(0)
    agg["estimated_cost_yen"] = agg["total_points"] * yen_per_point
    if drug_event is not None and not drug_event.empty and "drug_cost" in drug_event.columns:
        drug_cost = (
            drug_event.groupby("person_id")["drug_cost"]
            .sum()
            .rename("drug_cost_points")
        )
        agg = agg.merge(drug_cost, on="person_id", how="left")
        agg["drug_cost_points"] = agg["drug_cost_points"].fillna(0)
    out = out.merge(agg, on="person_id", how="left").fillna(0)
    out["total_points"] = out["total_points"].astype(int)
    out["inpatient_points"] = out["inpatient_points"].astype(int)
    out["outpatient_points"] = out["outpatient_points"].astype(int)
    return out
