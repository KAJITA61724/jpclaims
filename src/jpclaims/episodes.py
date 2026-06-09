"""Episode-level helpers (v0.1 stub for DPC episodes)."""

from __future__ import annotations

import pandas as pd


def build_inpatient_episodes(claims: pd.DataFrame) -> pd.DataFrame:
    """Build simplified inpatient episodes from claim-level data."""
    if claims is None or claims.empty:
        return pd.DataFrame(
            columns=["person_id", "episode_id", "admit_month", "discharge_month", "length_of_stay"]
        )
    inpatient = claims.copy()
    if "claim_type" in inpatient.columns:
        inpatient = inpatient[inpatient["claim_type"].astype(str).isin(["入院", "DPC"])]
    if inpatient.empty:
        return pd.DataFrame(
            columns=["person_id", "episode_id", "admit_month", "discharge_month", "length_of_stay"]
        )
    grouped = (
        inpatient.groupby(["person_id", "claim_month"], as_index=False)
        .agg(total_visit_days=("total_visit_days", "max"))
        .rename(columns={"claim_month": "admit_month"})
    )
    grouped["episode_id"] = grouped["person_id"].astype(str) + "_" + grouped["admit_month"].astype(str)
    grouped["discharge_month"] = grouped["admit_month"]
    grouped["length_of_stay"] = grouped["total_visit_days"].fillna(0)
    return grouped[
        ["person_id", "episode_id", "admit_month", "discharge_month", "length_of_stay"]
    ]
