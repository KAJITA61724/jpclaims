"""Monthly panel generation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.code_match import apply_group_definition
from jpclaims.dates import month_index_to_ym, ym_to_int, ym_to_month_index


def _month_range(start_ym: int, end_ym: int) -> list[int]:
    start = int(ym_to_month_index(pd.Series([start_ym])).iloc[0])
    end = int(ym_to_month_index(pd.Series([end_ym])).iloc[0])
    return [month_index_to_ym(i) for i in range(start, end + 1)]


def build_monthly_panel(
    person: pd.DataFrame,
    claim: pd.DataFrame | None = None,
    condition_event: pd.DataFrame | None = None,
    drug_event: pd.DataFrame | None = None,
    procedure_event: pd.DataFrame | None = None,
    visit_event: pd.DataFrame | None = None,
    code_definitions: dict[str, Any] | None = None,
    start_month: int | None = None,
    end_month: int | None = None,
    yen_per_point: float = 10.0,
) -> pd.DataFrame:
    defs = code_definitions or {}
    rows = []
    for _, p in person.iterrows():
        s = start_month or int(p["observation_start_ym"])
        e = end_month or int(p["observation_end_ym"])
        for month in _month_range(s, e):
            rows.append({"person_id": p["person_id"], "month": month})
    panel = pd.DataFrame(rows)
    if panel.empty:
        return panel

    source = claim if claim is not None else visit_event
    if source is not None and not source.empty:
        month_col = "claim_month" if "claim_month" in source.columns else "event_month"
        claim_agg = (
            source.groupby(["person_id", month_col])
            .agg(
                monthly_visit_count=("claim_id" if "claim_id" in source.columns else month_col, "nunique"),
                monthly_cost=(
                    "total_points",
                    lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum() * yen_per_point,
                )
                if "total_points" in source.columns
                else (month_col, "size"),
            )
            .reset_index()
            .rename(columns={month_col: "month"})
        )
        claim_agg["monthly_visit_flag"] = (claim_agg["monthly_visit_count"] > 0).astype(int)
        panel = panel.merge(claim_agg, on=["person_id", "month"], how="left")
    else:
        panel["monthly_visit_flag"] = 0
        panel["monthly_visit_count"] = 0
        panel["monthly_cost"] = 0.0

    for table, event_df, group_key, prefix in [
        ("condition", condition_event, "diagnosis_groups", "monthly_dx"),
        ("medication", drug_event, "medication_groups", "monthly_med"),
        ("procedure", procedure_event, "procedure_groups", "monthly_proc"),
    ]:
        groups = defs.get(group_key, {})
        if event_df is None or event_df.empty or not groups:
            continue
        event_df = event_df.copy()
        event_df["event_month"] = ym_to_int(event_df["event_month"])
        for group_name, definition in groups.items():
            matched = event_df.loc[apply_group_definition(event_df, definition)]
            if matched.empty:
                panel[f"{prefix}_{group_name}_flag"] = 0
                continue
            month_flags = (
                matched.groupby(["person_id", "event_month"])
                .size()
                .gt(0)
                .astype(int)
                .rename(f"{prefix}_{group_name}_flag")
                .reset_index()
                .rename(columns={"event_month": "month"})
            )
            panel = panel.merge(month_flags, on=["person_id", "month"], how="left")

    combo_groups = defs.get("cooccurrence_groups", {})
    if combo_groups:
        from jpclaims.features.cooccurrence import build_cooccurrence_features

        # monthly combo flags approximated via component month co-presence
        for group_name, definition in combo_groups.items():
            if definition.get("time_scope") != "same_month":
                continue
            components = definition.get("components", [])
            comp_months = []
            for comp in components:
                table = comp["table"]
                event_df = {
                    "condition_event": condition_event,
                    "drug_event": drug_event,
                    "procedure_event": procedure_event,
                }.get(table)
                group_defs = defs.get(
                    {
                        "condition_event": "diagnosis_groups",
                        "drug_event": "medication_groups",
                        "procedure_event": "procedure_groups",
                    }[table],
                    {},
                )
                definition_c = group_defs.get(comp["group"], {})
                if event_df is None or event_df.empty or not definition_c:
                    comp_months.append(pd.DataFrame(columns=["person_id", "month"]))
                    continue
                matched = event_df.loc[apply_group_definition(event_df, definition_c)].copy()
                matched["month"] = ym_to_int(matched["event_month"])
                comp_months.append(matched[["person_id", "month"]].drop_duplicates())
            if len(comp_months) >= 2:
                merged = comp_months[0]
                for nxt in comp_months[1:]:
                    merged = merged.merge(nxt, on=["person_id", "month"], how="inner")
                merged[f"monthly_combo_{group_name}_flag"] = 1
                panel = panel.merge(
                    merged[["person_id", "month", f"monthly_combo_{group_name}_flag"]],
                    on=["person_id", "month"],
                    how="left",
                )

    fill_zero = [c for c in panel.columns if c.endswith("_flag") or c.endswith("_count")]
    for col in fill_zero:
        panel[col] = panel[col].fillna(0).astype(int)
    if "monthly_cost" in panel.columns:
        panel["monthly_cost"] = panel["monthly_cost"].fillna(0.0)
    return panel
