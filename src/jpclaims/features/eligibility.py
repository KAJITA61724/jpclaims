"""Eligibility and observation features."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.windows import compute_window_availability, define_observation_window


def build_eligibility_features(
    person: pd.DataFrame,
    eligibility_rules: dict[str, Any] | None = None,
) -> pd.DataFrame:
    obs = define_observation_window(person.copy())
    out = obs[["person_id", "observed_months"]].copy()
    out = out.merge(compute_window_availability(person), on="person_id", how="left")
    rules = eligibility_rules or {}
    peds = rules.get("pediatric_cohort")
    if peds:
        birth_min = peds.get("birth_year_min")
        birth_max = peds.get("birth_year_max")
        min_obs = peds.get("min_observation_months", 12)
        require_dependent = peds.get("require_dependent", False)
        flags = pd.DataFrame({"person_id": person["person_id"]})
        if "birth_year" in person.columns and birth_min and birth_max:
            flags["birth_in_range_flag"] = person["birth_year"].between(birth_min, birth_max).astype(int)
        else:
            flags["birth_in_range_flag"] = 0
        flags["followup_flag"] = out["observed_months"].ge(min_obs).astype(int)
        if require_dependent and "self_family" in person.columns:
            flags["dependent_flag"] = (~person["self_family"].astype(str).str.contains("本人", na=False)).astype(int)
        else:
            flags["dependent_flag"] = 1
        flags["peds_eligible_flag"] = (
            flags["birth_in_range_flag"] & flags["followup_flag"] & flags["dependent_flag"]
        ).astype(int)
        out = out.merge(flags, on="person_id", how="left")
    return out
