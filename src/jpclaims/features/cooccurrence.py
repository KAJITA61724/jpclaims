"""Co-occurrence feature generation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.code_match import apply_group_definition
from jpclaims.dates import months_diff, ym_to_int
from jpclaims.features._base import _aggregate_event_features


def _resolve_group_events(
    table: str,
    group: str,
    events: dict[str, pd.DataFrame | None],
    definitions: dict[str, Any],
) -> pd.DataFrame:
    event_df = events.get(table)
    if event_df is None or event_df.empty:
        return pd.DataFrame()
    group_defs = definitions.get(f"{table.replace('_event', '')}_groups", {})
    if table == "condition_event":
        group_defs = definitions.get("diagnosis_groups", {})
    elif table == "drug_event":
        group_defs = definitions.get("medication_groups", {})
    elif table == "procedure_event":
        group_defs = definitions.get("procedure_groups", {})
    definition = group_defs.get(group, {})
    if not definition:
        return pd.DataFrame()
    matched = event_df.loc[apply_group_definition(event_df, definition)].copy()
    matched["__group__"] = group
    matched["__table__"] = table
    return matched


def _cooccur_same_patient(frames: list[pd.DataFrame]) -> pd.DataFrame:
    ids = [set(f["person_id"]) for f in frames if not f.empty]
    if not ids:
        return pd.DataFrame()
    common = set.intersection(*ids)
    out = pd.DataFrame({"person_id": list(common)})
    out["event_month"] = pd.NA
    out["source_claim_id"] = pd.NA
    return out


def _cooccur_same_month(frames: list[pd.DataFrame]) -> pd.DataFrame:
    keyed = []
    for f in frames:
        if f.empty:
            continue
        tmp = f[["person_id", "event_month"]].drop_duplicates()
        keyed.append(tmp)
    if len(keyed) < 2:
        return pd.DataFrame()
    merged = keyed[0]
    for nxt in keyed[1:]:
        merged = merged.merge(nxt, on=["person_id", "event_month"], how="inner")
    merged["source_claim_id"] = pd.NA
    return merged


def _cooccur_same_claim(frames: list[pd.DataFrame]) -> pd.DataFrame:
    keyed = []
    for f in frames:
        if f.empty or "source_claim_id" not in f.columns:
            continue
        tmp = f[["person_id", "event_month", "source_claim_id"]].drop_duplicates()
        keyed.append(tmp)
    if len(keyed) < 2:
        return pd.DataFrame()
    merged = keyed[0]
    for nxt in keyed[1:]:
        merged = merged.merge(
            nxt, on=["person_id", "event_month", "source_claim_id"], how="inner"
        )
    return merged


def build_cooccurrence_features(
    person: pd.DataFrame,
    events: dict[str, pd.DataFrame | None],
    definitions: dict[str, dict[str, Any]],
    code_definitions: dict[str, Any],
) -> pd.DataFrame:
    blocks = []
    for group_name, definition in definitions.items():
        components = definition.get("components", [])
        frames = []
        for comp in components:
            frames.append(
                _resolve_group_events(
                    comp["table"], comp["group"], events, code_definitions
                )
            )
        scope = definition.get("time_scope", "same_patient")
        if scope == "same_month":
            co = _cooccur_same_month(frames)
        elif scope == "same_claim":
            co = _cooccur_same_claim(frames)
        else:
            co = _cooccur_same_patient(frames)
        pseudo_def = {"output": definition.get("output", {})}
        block = _aggregate_event_features(person, co, group_name, "combo", pseudo_def)
        output_cfg = definition.get("output", {})
        if output_cfg.get("incident"):
            washout = int(output_cfg["incident"].get("washout_months", 6))
            first_col = f"combo_{group_name}_first_ym_obs"
            flag_col = f"combo_{group_name}_flag_obs"
            if first_col in block.columns:
                gap = months_diff(person["observation_start_ym"], block[first_col])
                block[f"combo_{group_name}_incident_{washout}m_flag"] = (
                    block[flag_col].eq(1) & gap.ge(washout)
                ).astype(int)
        blocks.append(block)
    if not blocks:
        return person[["person_id"]].copy()
    out = blocks[0]
    for block in blocks[1:]:
        out = out.merge(block, on="person_id", how="left")
    return out


def extract_cooccurring_codes(
    target_events: pd.DataFrame,
    context_events: pd.DataFrame,
    target_definition: dict[str, Any],
    context_code_columns: list[str],
    scope: str = "same_claim",
) -> pd.DataFrame:
    """Extract long-format co-occurring code pairs."""
    target = target_events.loc[apply_group_definition(target_events, target_definition)].copy()
    if target.empty or context_events.empty:
        return pd.DataFrame(
            columns=[
                "person_id",
                "target_group",
                "target_table",
                "target_code",
                "context_table",
                "context_code_column",
                "context_code",
                "context_name",
                "cooccur_count",
                "first_ym",
                "last_ym",
            ]
        )
    join_keys = ["person_id"]
    if scope in {"same_month", "same_claim", "within_months"}:
        join_keys.append("event_month")
    if scope == "same_claim":
        join_keys.append("source_claim_id")
    merged = target.merge(context_events, on=join_keys, suffixes=("_target", "_context"))
    rows = []
    for col in context_code_columns:
        if col not in merged.columns:
            continue
        name_col = col.replace("_code", "_name")
        if name_col not in merged.columns:
            name_col = None
        grouped = merged.groupby(["person_id", col], dropna=False)
        for (person_id, code), grp in grouped:
            rows.append(
                {
                    "person_id": person_id,
                    "target_group": target_definition.get("group", "target"),
                    "target_table": "target",
                    "target_code": grp.get("diagnosis_code", pd.Series([pd.NA])).iloc[0],
                    "context_table": "context",
                    "context_code_column": col,
                    "context_code": code,
                    "context_name": grp[name_col].iloc[0] if name_col else pd.NA,
                    "cooccur_count": len(grp),
                    "first_ym": ym_to_int(grp["event_month"]).min(),
                    "last_ym": ym_to_int(grp["event_month"]).max(),
                }
            )
    return pd.DataFrame(rows)


def summarize_cooccurring_codes_by_patient(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    return (
        long_df.groupby(["person_id", "context_code_column", "context_code"], as_index=False)
        .agg(
            cooccur_count=("cooccur_count", "sum"),
            first_ym=("first_ym", "min"),
            last_ym=("last_ym", "max"),
        )
    )


def summarize_codes_by_window(
    long_df: pd.DataFrame,
    person: pd.DataFrame,
    start_offset: int,
    end_offset: int,
    index_dates: pd.DataFrame,
) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    idx = index_dates[["person_id", "index_ym"]]
    merged = long_df.merge(idx, on="person_id", how="left")
    from jpclaims.dates import ym_to_month_index

    rel = ym_to_month_index(merged["first_ym"]) - ym_to_month_index(merged["index_ym"])
    windowed = merged.loc[rel.between(start_offset, end_offset)]
    return summarize_cooccurring_codes_by_patient(windowed)
