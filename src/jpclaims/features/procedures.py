"""Procedure feature generation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.code_match import apply_group_definition
from jpclaims.features._base import _aggregate_event_features
from jpclaims.windows import filter_by_observation_window


def build_procedure_features(
    person: pd.DataFrame,
    procedure_event: pd.DataFrame | None,
    definitions: dict[str, Any],
) -> pd.DataFrame:
    blocks = []
    for group_name, definition in definitions.items():
        block = _aggregate_event_features(
            person, procedure_event, group_name, "proc", definition
        )
        if procedure_event is not None and not procedure_event.empty:
            matched = procedure_event.loc[apply_group_definition(procedure_event, definition)]
            obs = filter_by_observation_window(matched, person)
            if not obs.empty and "points" in obs.columns:
                pts = (
                    obs.groupby("person_id")["points"]
                    .sum()
                    .rename(f"proc_{group_name}_total_points_obs")
                )
                block = block.merge(pts, on="person_id", how="left")
                block[f"proc_{group_name}_total_points_obs"] = block[
                    f"proc_{group_name}_total_points_obs"
                ].fillna(0)
        blocks.append(block)
    if not blocks:
        return person[["person_id"]].copy()
    out = blocks[0]
    for block in blocks[1:]:
        out = out.merge(block, on="person_id", how="left")
    return out
