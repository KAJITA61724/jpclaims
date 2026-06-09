"""Pre-release safety and regression tests."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from jpclaims import build_patient_datamart, load_code_definitions, normalize_events
from jpclaims.config import definition_hash
from jpclaims.features.cooccurrence import build_cooccurrence_features
from jpclaims.qc import generate_qc_report

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "jpclaims"
SAMPLE_DIR = ROOT / "examples" / "sample_data"

STUDY_CODE_PATTERN = re.compile(
    r"8848201|K52\.2|FPIES|fpies|190178210|190178310|160180410"
)


def test_fake_sample_csv_is_readable():
    """Only whitelisted synthetic CSV paths should exist and load."""
    expected = [
        "patients.csv",
        "claims.csv",
        "diagnoses.csv",
        "medications.csv",
        "procedures.csv",
    ]
    for name in expected:
        path = SAMPLE_DIR / name
        assert path.exists(), f"missing fixture: {path}"
        df = pd.read_csv(path)
        assert len(df) > 0
        assert not df["加入者id" if "加入者id" in df.columns else df.columns[0]].astype(str).str.match(
            r"^\d{10,}$"
        ).any(), "IDs look like real numeric subscriber IDs"


def test_no_study_specific_codes_in_src():
    """Library core must not hardcode study-specific disease or procedure codes."""
    hits: list[str] = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if STUDY_CODE_PATTERN.search(text):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], f"study-specific codes found in src: {hits}"


def test_first_last_ym_not_zero_filled(fake_person, fake_conditions, minimal_defs):
    dm, _ = build_patient_datamart(
        person=fake_person,
        condition_event=fake_conditions,
        code_definitions=minimal_defs,
        return_report=True,
    )
    p2 = dm.loc[dm.person_id == "P002"].iloc[0]
    assert pd.isna(p2["dx_fpies_name_first_ym_obs"])
    p1 = dm.loc[dm.person_id == "P001"].iloc[0]
    assert int(p1["dx_fpies_name_first_ym_obs"]) == 202003


def test_flag_columns_are_binary_int(fake_person, fake_claims, minimal_defs):
    dm, _ = build_patient_datamart(
        person=fake_person,
        claim=fake_claims,
        code_definitions=minimal_defs,
        return_report=True,
    )
    flag_cols = [c for c in dm.columns if c.endswith("_flag") or c.endswith("_flag_obs")]
    for col in flag_cols:
        vals = dm[col].dropna().unique()
        assert set(vals).issubset({0, 1}), f"{col} has non-binary values: {vals}"
        assert dm[col].dtype in ("int64", "int32", "Int64", "int8", "uint8")


def test_count_columns_are_zero_int(fake_person, fake_claims, minimal_defs):
    dm, _ = build_patient_datamart(
        person=fake_person,
        claim=fake_claims,
        code_definitions=minimal_defs,
        return_report=True,
    )
    count_cols = [c for c in dm.columns if "_count" in c]
    for col in count_cols:
        assert (dm[col].fillna(0) >= 0).all()
        assert dm[col].dtype in ("int64", "int32", "Int64", "float64")


def test_same_month_cooccurrence(fake_person, fake_conditions, fake_procedures, minimal_defs):
    events = {
        "condition_event": fake_conditions,
        "drug_event": None,
        "procedure_event": fake_procedures,
    }
    out = build_cooccurrence_features(
        fake_person, events, minimal_defs["cooccurrence_groups"], minimal_defs
    )
    assert out.loc[out.person_id == "P001", "combo_fpies_ofc_same_month_flag_obs"].iloc[0] == 1
    assert out.loc[out.person_id == "P003", "combo_fpies_ofc_same_month_flag_obs"].iloc[0] == 0


def test_same_claim_cooccurrence(fake_person, fake_conditions, fake_procedures):
    defs = {
        "diagnosis_groups": {
            "dx_a": {
                "code_column": "diagnosis_code",
                "codes": ["8848201"],
                "match": "exact",
            }
        },
        "procedure_groups": {
            "proc_a": {
                "code_column": "procedure_code",
                "codes": ["160180410"],
                "match": "exact",
            }
        },
        "cooccurrence_groups": {
            "dx_proc_same_claim": {
                "time_scope": "same_claim",
                "components": [
                    {"table": "condition_event", "group": "dx_a"},
                    {"table": "procedure_event", "group": "proc_a"},
                ],
            }
        },
    }
    events = {
        "condition_event": fake_conditions,
        "procedure_event": fake_procedures,
    }
    out = build_cooccurrence_features(fake_person, events, defs["cooccurrence_groups"], defs)
    assert out.loc[out.person_id == "P001", "combo_dx_proc_same_claim_flag_obs"].iloc[0] == 1


def test_washout_incident_flag_positive():
    person = pd.DataFrame(
        {
            "person_id": ["W1"],
            "observation_start_ym": [201801],
            "observation_end_ym": [202412],
        }
    )
    conditions = pd.DataFrame(
        {
            "person_id": ["W1"],
            "event_month": [201901],
            "diagnosis_code": ["8848201"],
            "icd10_code": ["K52.2"],
            "suspected_flag": [0],
            "primary_flag": [1],
            "source_claim_id": ["C1"],
        }
    )
    defs = {
        "diagnosis_groups": {
            "incident_dx": {
                "code_column": "diagnosis_code",
                "codes": ["8848201"],
                "match": "exact",
                "output": {"incident": {"washout_months": 6}},
            }
        }
    }
    dm, _ = build_patient_datamart(
        person=person,
        condition_event=conditions,
        code_definitions=defs,
        return_report=True,
    )
    assert dm["dx_incident_dx_incident_6m_flag"].iloc[0] == 1


def test_yaml_definition_hash_in_qc(fake_person, minimal_defs):
    defs = dict(minimal_defs)
    defs["_definition_hash"] = definition_hash(defs)
    dm = pd.DataFrame({"person_id": fake_person["person_id"]})
    report = generate_qc_report(
        input_tables={"person": fake_person},
        output=dm,
        code_definitions=defs,
    )
    assert report["code_definition_hash"]
    assert len(report["code_definition_hash"]) >= 8


def test_gitignore_blocks_real_data_patterns():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ["data/", "outputs/", "*.parquet", ".env", "*.csv"]:
        assert pattern in gitignore
    assert "!examples/sample_data/*.csv" in gitignore


PLACEHOLDER_URL_PATTERN = re.compile(
    r"github\.com/example|example/jpclaims|YOUR_ORG|your-org|placeholder",
    re.IGNORECASE,
)


def test_no_placeholder_urls_in_release_metadata():
    """Public-facing metadata must not contain template repository URLs."""
    targets = [
        ROOT / "pyproject.toml",
        ROOT / "README.md",
        *ROOT.glob("docs/*.md"),
    ]
    hits: list[str] = []
    for path in targets:
        text = path.read_text(encoding="utf-8")
        if PLACEHOLDER_URL_PATTERN.search(text):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], f"placeholder URLs found in: {hits}"

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "github.com/KAJITA61724/jpclaims" in pyproject
