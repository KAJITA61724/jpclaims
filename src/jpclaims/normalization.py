"""Raw-to-standard event normalization."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.dates import ym_to_int
from jpclaims.io import preserve_string_codes
from jpclaims.schema import get_schema
from jpclaims.validation import validate_events


def _rename_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    present = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=present)


def _derive_birth_year(person: pd.DataFrame) -> pd.DataFrame:
    out = person.copy()
    if "birth_ym" in out.columns and "birth_year" not in out.columns:
        out["birth_year"] = (ym_to_int(out["birth_ym"]) // 100).astype("Int64")
    return out


def _derive_visit_events(claims: pd.DataFrame) -> pd.DataFrame:
    out = claims.copy()
    claim_type = out.get("claim_type", pd.Series("", index=out.index)).astype(str)
    out["inpatient_flag"] = claim_type.isin(["入院", "DPC"]).astype(int)
    out["outpatient_flag"] = claim_type.isin(["外来", "入院外"]).astype(int)
    out["dispensing_flag"] = claim_type.str.contains("調剤", na=False).astype(int)
    out["setting"] = claim_type
    if "claim_month" in out.columns:
        out["event_month"] = out["claim_month"]
    cols = [
        "person_id",
        "event_month",
        "setting",
        "inpatient_flag",
        "outpatient_flag",
        "dispensing_flag",
        "facility_id",
        "department",
        "claim_id",
    ]
    rename = {"claim_id": "source_claim_id"}
    result = out[[c for c in cols if c in out.columns]].rename(columns=rename)
    return result


def _derive_checkup_month(checkups: pd.DataFrame) -> pd.DataFrame:
    out = checkups.copy()
    if "checkup_date_raw" in out.columns:
        raw = pd.to_numeric(out["checkup_date_raw"], errors="coerce")
        out["checkup_month"] = (raw // 100).astype("Int64")
    elif "checkup_month" not in out.columns:
        out["checkup_month"] = pd.NA
    return out


def normalize_events(
    patients: pd.DataFrame | None = None,
    claims: pd.DataFrame | None = None,
    diagnoses: pd.DataFrame | None = None,
    medications: pd.DataFrame | None = None,
    procedures: pd.DataFrame | None = None,
    checkups: pd.DataFrame | None = None,
    column_map: dict[str, dict[str, str]] | None = None,
    schema: str = "jp_generic",
    validate: bool = True,
) -> dict[str, pd.DataFrame]:
    """Convert Japanese raw tables to the standard event model."""
    schema_def = get_schema(schema)
    cmap = column_map or schema_def["column_map"]
    events: dict[str, pd.DataFrame | None] = {
        "person": None,
        "claim": None,
        "condition_event": None,
        "drug_event": None,
        "procedure_event": None,
        "visit_event": None,
        "checkup_event": None,
    }

    if patients is not None:
        person = _rename_columns(patients, cmap.get("person", {}))
        person = _derive_birth_year(person)
        events["person"] = preserve_string_codes(person, "person")

    if claims is not None:
        claim = _rename_columns(claims, cmap.get("claim", {}))
        events["claim"] = preserve_string_codes(claim, "claim")
        events["visit_event"] = preserve_string_codes(_derive_visit_events(claim), "visit_event")

    if diagnoses is not None:
        cond = _rename_columns(diagnoses, cmap.get("condition_event", {}))
        events["condition_event"] = preserve_string_codes(cond, "condition_event")

    if medications is not None:
        drug = _rename_columns(medications, cmap.get("drug_event", {}))
        events["drug_event"] = preserve_string_codes(drug, "drug_event")

    if procedures is not None:
        proc = _rename_columns(procedures, cmap.get("procedure_event", {}))
        events["procedure_event"] = preserve_string_codes(proc, "procedure_event")

    if checkups is not None:
        chk = _rename_columns(checkups, cmap.get("checkup_event", {}))
        chk = _derive_checkup_month(chk)
        events["checkup_event"] = preserve_string_codes(chk, "checkup_event")

    if validate:
        issues = validate_events({k: v for k, v in events.items() if v is not None})
        for table, table_issues in issues.items():
            if table_issues:
                raise ValueError(f"Validation failed for {table}: {table_issues}")

    return {k: v for k, v in events.items() if v is not None}
