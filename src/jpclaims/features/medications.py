"""Medication feature generation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.code_match import apply_group_definition
from jpclaims.dates import months_diff, ym_to_int
from jpclaims.features._base import _aggregate_event_features
from jpclaims.windows import filter_by_observation_window


def build_medication_features(
    person: pd.DataFrame,
    drug_event: pd.DataFrame | None,
    definitions: dict[str, Any],
) -> pd.DataFrame:
    blocks = []
    for group_name, definition in definitions.items():
        block = _aggregate_event_features(person, drug_event, group_name, "med", definition)
        if drug_event is not None and not drug_event.empty:
            matched = drug_event.loc[apply_group_definition(drug_event, definition)].copy()
            obs = filter_by_observation_window(matched, person)
            if not obs.empty and "days_supply" in obs.columns:
                days = (
                    obs.groupby("person_id")["days_supply"]
                    .sum()
                    .rename(f"med_{group_name}_total_days_obs")
                )
                block = block.merge(days, on="person_id", how="left")
                block[f"med_{group_name}_total_days_obs"] = block[
                    f"med_{group_name}_total_days_obs"
                ].fillna(0)
            if not obs.empty and "quantity" in obs.columns:
                qty = (
                    obs.groupby("person_id")["quantity"]
                    .sum()
                    .rename(f"med_{group_name}_total_quantity_obs")
                )
                block = block.merge(qty, on="person_id", how="left")
                block[f"med_{group_name}_total_quantity_obs"] = block[
                    f"med_{group_name}_total_quantity_obs"
                ].fillna(0)
            if not obs.empty and "drug_cost" in obs.columns:
                cost = (
                    obs.groupby("person_id")["drug_cost"]
                    .sum()
                    .rename(f"med_{group_name}_total_cost_obs")
                )
                block = block.merge(cost, on="person_id", how="left")
                block[f"med_{group_name}_total_cost_obs"] = block[
                    f"med_{group_name}_total_cost_obs"
                ].fillna(0)

            output_cfg = definition.get("output", {})
            washout = output_cfg.get("incident", {}).get("washout_months", 6)
            first_col = f"med_{group_name}_first_ym_obs"
            flag_col = f"med_{group_name}_flag_obs"
            if first_col in block.columns:
                gap = months_diff(
                    block["person_id"].map(person.set_index("person_id")["observation_start_ym"]),
                    block[first_col],
                )
                block[f"med_{group_name}_new_user_flag"] = (
                    block[flag_col].eq(1) & gap.ge(washout)
                ).astype(int)
                block[f"med_{group_name}_washout_clean_flag"] = block[
                    f"med_{group_name}_new_user_flag"
                ]
        blocks.append(block)
    if not blocks:
        return person[["person_id"]].copy()
    out = blocks[0]
    for block in blocks[1:]:
        out = out.merge(block, on="person_id", how="left")
    return out
