"""Shared feature aggregation utilities."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.code_match import apply_group_definition
from jpclaims.dates import months_between, months_diff, ym_to_int
from jpclaims.windows import filter_by_observation_window, months_from_obs_start


def _empty_feature_frame(person: pd.DataFrame, prefix: str, group: str) -> pd.DataFrame:
    return pd.DataFrame({"person_id": person["person_id"].unique()})


def _aggregate_event_features(
    person: pd.DataFrame,
    events: pd.DataFrame,
    group_name: str,
    prefix: str,
    definition: dict[str, Any],
    month_col: str = "event_month",
    claim_col: str = "source_claim_id",
) -> pd.DataFrame:
    """Aggregate standard flag/count/first/last/month features for matched events."""
    base = person[["person_id", "observation_start_ym", "observation_end_ym"]].copy()
    if events is None or events.empty:
        return _zero_features(base, group_name, prefix)

    matched = events.copy()
    has_match_keys = any(k in definition for k in ("code_column", "name_column", "rules", "codes"))
    if has_match_keys:
        matched = events.loc[apply_group_definition(events, definition)].copy()
    if matched.empty:
        return _zero_features(base, group_name, prefix)

    matched[month_col] = ym_to_int(matched[month_col])
    all_agg = (
        matched.groupby("person_id")
        .agg(
            **{
                f"{prefix}_{group_name}_count_all": (month_col, "size"),
                f"{prefix}_{group_name}_claim_count_all": (claim_col, "nunique")
                if claim_col in matched.columns
                else (month_col, "size"),
                f"{prefix}_{group_name}_month_count_all": (month_col, "nunique"),
                f"{prefix}_{group_name}_first_ym_all": (month_col, "min"),
                f"{prefix}_{group_name}_last_ym_all": (month_col, "max"),
            }
        )
        .reset_index()
    )

    obs_matched = filter_by_observation_window(matched, person, month_col=month_col)
    if obs_matched.empty:
        obs_agg = base[["person_id"]].copy()
        obs_agg[f"{prefix}_{group_name}_flag_obs"] = 0
        obs_agg[f"{prefix}_{group_name}_count_obs"] = 0
        obs_agg[f"{prefix}_{group_name}_claim_count_obs"] = 0
        obs_agg[f"{prefix}_{group_name}_month_count_obs"] = 0
        obs_agg[f"{prefix}_{group_name}_first_ym_obs"] = pd.NA
        obs_agg[f"{prefix}_{group_name}_last_ym_obs"] = pd.NA
    else:
        obs_agg = (
            obs_matched.groupby("person_id")
            .agg(
                **{
                    f"{prefix}_{group_name}_count_obs": (month_col, "size"),
                    f"{prefix}_{group_name}_claim_count_obs": (claim_col, "nunique")
                    if claim_col in obs_matched.columns
                    else (month_col, "size"),
                    f"{prefix}_{group_name}_month_count_obs": (month_col, "nunique"),
                    f"{prefix}_{group_name}_first_ym_obs": (month_col, "min"),
                    f"{prefix}_{group_name}_last_ym_obs": (month_col, "max"),
                }
            )
            .reset_index()
        )
        obs_agg[f"{prefix}_{group_name}_flag_obs"] = 1

    out = base.merge(all_agg, on="person_id", how="left").merge(obs_agg, on="person_id", how="left")
    flag_col = f"{prefix}_{group_name}_flag_obs"
    out[flag_col] = out[flag_col].fillna(0).astype(int)

    count_cols = [c for c in out.columns if c.endswith("_count_all") or c.endswith("_count_obs")]
    for col in count_cols:
        out[col] = out[col].fillna(0).astype(int)

    claim_cols = [c for c in out.columns if "_claim_count_" in c]
    for col in claim_cols:
        out[col] = out[col].fillna(0).astype(int)

    month_cols = [c for c in out.columns if "_month_count_" in c]
    for col in month_cols:
        out[col] = out[col].fillna(0).astype(int)

    first_all = f"{prefix}_{group_name}_first_ym_all"
    last_all = f"{prefix}_{group_name}_last_ym_all"
    first_obs = f"{prefix}_{group_name}_first_ym_obs"
    last_obs = f"{prefix}_{group_name}_last_ym_obs"
    out[f"{prefix}_{group_name}_duration_months_all"] = months_between(
        out[first_all], out[last_all]
    ).fillna(0).astype(int)
    out[f"{prefix}_{group_name}_duration_months_obs"] = months_between(
        out[first_obs], out[last_obs]
    ).fillna(0).astype(int)
    out[f"{prefix}_{group_name}_months_from_obs_start"] = months_from_obs_start(
        person, out[first_obs]
    )

    output_cfg = definition.get("output", {})
    if output_cfg.get("incident"):
        washout = int(output_cfg["incident"].get("washout_months", 6))
        incident_col = f"{prefix}_{group_name}_incident_{washout}m_flag"
        months_gap = months_diff(
            out["person_id"].map(person.set_index("person_id")["observation_start_ym"]),
            out[first_obs],
        )
        out[incident_col] = (
            out[flag_col].eq(1) & months_gap.ge(washout)
        ).astype(int)

    if "suspected_flag" in matched.columns:
        suspected = matched.copy()
        suspected_val = pd.to_numeric(suspected["suspected_flag"], errors="coerce").fillna(0)
        suspected_counts = (
            suspected.loc[suspected_val.eq(1)]
            .groupby("person_id")
            .size()
            .rename(f"{prefix}_{group_name}_suspected_count")
        )
        confirmed_counts = (
            suspected.loc[suspected_val.eq(0)]
            .groupby("person_id")
            .size()
            .rename(f"{prefix}_{group_name}_confirmed_count")
        )
        out = out.merge(suspected_counts, on="person_id", how="left")
        out = out.merge(confirmed_counts, on="person_id", how="left")
        for col in [f"{prefix}_{group_name}_suspected_count", f"{prefix}_{group_name}_confirmed_count"]:
            if col in out.columns:
                out[col] = out[col].fillna(0).astype(int)

    if definition.get("primary_only") and "primary_flag" in matched.columns:
        primary = (
            matched.loc[pd.to_numeric(matched["primary_flag"], errors="coerce").fillna(0).eq(1)]
            .groupby("person_id")
            .size()
        )
        out[f"{prefix}_{group_name}_main_disease_flag"] = (
            out["person_id"].isin(primary.index).astype(int)
        )

    return out.drop(columns=["observation_start_ym", "observation_end_ym"], errors="ignore")


def _zero_features(base: pd.DataFrame, group_name: str, prefix: str) -> pd.DataFrame:
    out = base[["person_id"]].copy()
    out[f"{prefix}_{group_name}_flag_obs"] = 0
    out[f"{prefix}_{group_name}_count_obs"] = 0
    out[f"{prefix}_{group_name}_claim_count_obs"] = 0
    out[f"{prefix}_{group_name}_month_count_obs"] = 0
    out[f"{prefix}_{group_name}_count_all"] = 0
    out[f"{prefix}_{group_name}_claim_count_all"] = 0
    out[f"{prefix}_{group_name}_month_count_all"] = 0
    out[f"{prefix}_{group_name}_first_ym_all"] = pd.NA
    out[f"{prefix}_{group_name}_last_ym_all"] = pd.NA
    out[f"{prefix}_{group_name}_first_ym_obs"] = pd.NA
    out[f"{prefix}_{group_name}_last_ym_obs"] = pd.NA
    out[f"{prefix}_{group_name}_duration_months_all"] = 0
    out[f"{prefix}_{group_name}_duration_months_obs"] = 0
    out[f"{prefix}_{group_name}_months_from_obs_start"] = pd.NA
    return out


def merge_feature_blocks(person: pd.DataFrame, blocks: list[pd.DataFrame]) -> pd.DataFrame:
    out = person[["person_id"]].drop_duplicates().copy()
    for block in blocks:
        if block is None or block.empty:
            continue
        cols = [c for c in block.columns if c != "person_id"]
        out = out.merge(block[["person_id", *cols]], on="person_id", how="left")
    return out
