"""Demographic features."""

from __future__ import annotations

import pandas as pd

from jpclaims.dates import ym_to_int


def build_demographic_features(person: pd.DataFrame, reference_ym: int | None = None) -> pd.DataFrame:
    out = person[["person_id"]].copy()
    ref = reference_ym or int(person["observation_end_ym"].max())
    if "sex" in person.columns:
        out["sex"] = pd.to_numeric(person["sex"], errors="coerce")
    if "birth_ym" in person.columns:
        birth = ym_to_int(person["birth_ym"])
        out["birth_ym"] = birth
        out["birth_year"] = (birth // 100).astype("Int64")
        ref_year = ref // 100
        ref_month = ref % 100
        birth_year = birth // 100
        birth_month = birth % 100
        out["age"] = ref_year - birth_year - (ref_month < birth_month).astype(int)
        out["age_group"] = pd.cut(
            out["age"],
            bins=[-1, 18, 40, 65, 120],
            labels=["0-17", "18-39", "40-64", "65+"],
        ).astype(str)
    for col in ["insurance_type", "family_id", "relationship", "self_family", "death_flag"]:
        if col in person.columns:
            out[col] = person[col]
    return out
