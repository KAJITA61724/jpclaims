"""Patient-level datamart builder."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.config import definition_hash
from jpclaims.features import (
    assign_exclusive_group,
    assign_phenotype_group,
    build_cooccurrence_features,
    build_comorbidity_score,
    build_composite_features,
    build_cost_features,
    build_demographic_features,
    build_diagnosis_features,
    build_eligibility_features,
    build_health_checkup_features,
    build_medication_features,
    build_procedure_features,
    build_utilization_features,
)
from jpclaims.qc import generate_qc_report
from jpclaims.windows import define_observation_window


def build_patient_datamart(
    person: pd.DataFrame,
    claim: pd.DataFrame | None = None,
    condition_event: pd.DataFrame | None = None,
    drug_event: pd.DataFrame | None = None,
    procedure_event: pd.DataFrame | None = None,
    visit_event: pd.DataFrame | None = None,
    checkup_event: pd.DataFrame | None = None,
    code_definitions: dict[str, Any] | None = None,
    index_dates: pd.DataFrame | None = None,
    windows: dict[str, Any] | None = None,
    yen_per_point: float = 10.0,
    return_report: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    """Build a one-row-per-patient analysis datamart."""
    defs = code_definitions or {}
    person_obs = define_observation_window(person.copy())
    events = {
        "condition_event": condition_event,
        "drug_event": drug_event,
        "procedure_event": procedure_event,
        "visit_event": visit_event,
        "claim": claim,
    }

    blocks = [
        build_demographic_features(person_obs),
        build_eligibility_features(person_obs, defs.get("eligibility_rules")),
        build_diagnosis_features(person_obs, condition_event, defs.get("diagnosis_groups", {})),
        build_medication_features(person_obs, drug_event, defs.get("medication_groups", {})),
        build_procedure_features(person_obs, procedure_event, defs.get("procedure_groups", {})),
        build_cooccurrence_features(
            person_obs, events, defs.get("cooccurrence_groups", {}), defs
        ),
        build_utilization_features(person_obs, claim, visit_event),
        build_cost_features(person_obs, claim, drug_event, yen_per_point=yen_per_point),
        build_health_checkup_features(checkup_event, person_obs),
        build_comorbidity_score(
            person_obs,
            condition_event,
            defs.get("comorbidity_groups", {}),
            defs.get("comorbidity_weights"),
        ),
    ]

    dm = person_obs[["person_id"]].drop_duplicates().copy()
    for block in blocks:
        dm = dm.merge(block, on="person_id", how="left")

    dm = build_composite_features(dm, defs.get("composite_features", {}))
    for group_name, group_def in defs.get("exclusive_groups", {}).items():
        dm = assign_exclusive_group(
            dm,
            group_name,
            group_def.get("rules", []),
            default=group_def.get("default", "other"),
        )
    if defs.get("phenotype_groups"):
        dm = assign_phenotype_group(dm, defs["phenotype_groups"])

    if index_dates is not None and not index_dates.empty:
        dm = dm.merge(index_dates, on="person_id", how="left")

    dm = _finalize_types(dm)

    report = generate_qc_report(
        input_tables={
            "person": person,
            "claim": claim,
            "condition_event": condition_event,
            "drug_event": drug_event,
            "procedure_event": procedure_event,
        },
        output=dm,
        code_definitions=defs,
        definition_hit_counts=_definition_hit_counts(dm, defs),
    )
    if return_report:
        return dm, report
    return dm


def _finalize_types(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col.endswith("_flag") or col.endswith("_flag_obs") or col.startswith("cm_") and col.endswith("_flag"):
            out[col] = out[col].fillna(0).astype(int)
        elif col.endswith("_count") or col.endswith("_count_obs") or col.endswith("_count_all"):
            out[col] = out[col].fillna(0).astype(int)
        elif col.endswith("_months") or col.endswith("_score"):
            out[col] = out[col].fillna(0)
        elif col.endswith("_ym") or col.endswith("_ym_all") or col.endswith("_ym_obs"):
            pass
    return out


def _definition_hit_counts(dm: pd.DataFrame, defs: dict[str, Any]) -> dict[str, int]:
    hits: dict[str, int] = {}
    for key, prefix in [
        ("diagnosis_groups", "dx"),
        ("medication_groups", "med"),
        ("procedure_groups", "proc"),
        ("cooccurrence_groups", "combo"),
    ]:
        for group in defs.get(key, {}):
            col = f"{prefix}_{group}_flag_obs"
            if col in dm.columns:
                hits[col] = int(dm[col].sum())
    return hits
