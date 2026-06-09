"""Comorbidity score framework."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.code_match import apply_group_definition


def build_comorbidity_score(
    person: pd.DataFrame,
    condition_event: pd.DataFrame | None,
    comorbidity_groups: dict[str, Any],
    weights: dict[str, int] | None = None,
    score_name: str = "charlson_score",
) -> pd.DataFrame:
    """Build a weighted comorbidity score from external YAML definitions."""
    out = person[["person_id"]].copy()
    if condition_event is None or condition_event.empty or not comorbidity_groups:
        out[score_name] = 0
        return out
    score = pd.Series(0, index=out.index)
    for group_name, definition in comorbidity_groups.items():
        weight = (weights or {}).get(group_name, definition.get("weight", 1))
        matched_ids = condition_event.loc[
            apply_group_definition(condition_event, definition), "person_id"
        ].unique()
        flag = out["person_id"].isin(matched_ids).astype(int) * weight
        out[f"cm_{group_name}_flag"] = out["person_id"].isin(matched_ids).astype(int)
        score = score + flag
    out[score_name] = score.astype(int)
    return out
