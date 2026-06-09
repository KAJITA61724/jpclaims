"""README Quickstart regression test."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from jpclaims import build_patient_datamart, load_code_definitions, normalize_events

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_data"


def test_readme_quickstart_builds_datamart_with_report():
    """Mirror README Quick start: sample CSVs -> normalize -> datamart + QC."""
    defs = load_code_definitions(ROOT / "examples" / "minimal_code_definitions.yaml")
    events = normalize_events(
        patients=pd.read_csv(SAMPLE / "patients.csv"),
        claims=pd.read_csv(SAMPLE / "claims.csv"),
        diagnoses=pd.read_csv(SAMPLE / "diagnoses.csv"),
        medications=pd.read_csv(SAMPLE / "medications.csv"),
        procedures=pd.read_csv(SAMPLE / "procedures.csv"),
    )
    dm, report = build_patient_datamart(
        person=events["person"],
        claim=events["claim"],
        condition_event=events["condition_event"],
        drug_event=events["drug_event"],
        procedure_event=events["procedure_event"],
        code_definitions=defs,
        return_report=True,
    )

    assert len(dm) == 3
    assert dm["person_id"].nunique() == 3
    assert dm["person_id"].duplicated().sum() == 0
    assert report["patient_retention_check"] == 1.0
    assert report["output_row_count"] == 3
    assert "dx_diabetes_flag_obs" in dm.columns
    assert report["code_definition_hash"]
