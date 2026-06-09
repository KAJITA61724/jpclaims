"""Shared fake data fixtures for jpclaims tests."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def fake_person() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["P001", "P002", "P003"],
            "sex": [1, 2, 1],
            "birth_ym": [201806, 198005, 201512],
            "observation_start_ym": [202001, 201901, 202006],
            "observation_end_ym": [202412, 202312, 202412],
            "death_flag": [0, 0, 0],
            "insurance_type": ["組合", "組合", "組合"],
            "family_id": ["F1", "F2", "F1"],
            "relationship": ["子", "本人", "子"],
            "self_family": ["家族", "本人", "家族"],
        }
    )


@pytest.fixture
def fake_claims() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "claim_id": ["C1", "C2", "C3", "C4", "C5"],
            "person_id": ["P001", "P001", "P002", "P002", "P003"],
            "claim_month": [202003, 202004, 202001, 202002, 202101],
            "claim_type": ["外来", "入院", "外来", "外来", "外来"],
            "facility_id": ["H1", "H1", "H2", "H2", "H1"],
            "department": ["小児科", "小児科", "内科", "内科", "小児科"],
            "total_points": [1200, 5000, 800, 900, 600],
            "total_visit_days": [1, 3, 1, 1, 1],
        }
    )


@pytest.fixture
def fake_conditions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["P001", "P001", "P002", "P003", "P003"],
            "event_month": [202003, 202008, 202001, 202101, 202102],
            "diagnosis_code": ["8848201", "8848201", "010", "E110", "I10"],
            "diagnosis_name": ["FPIES", "食物蛋白誘発胃腸炎", "感冒", "2型糖尿病", "本態性高血圧"],
            "icd10_code": ["K52.2", "K52.2", "J00", "E11", "I10"],
            "suspected_flag": [0, 0, 0, 0, 1],
            "primary_flag": [1, 0, 1, 1, 1],
            "source_claim_id": ["C1", "C1", "C3", "C5", "C5"],
        }
    )


@pytest.fixture
def fake_drugs() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["P001", "P001", "P002", "P003"],
            "event_month": [202003, 202004, 202001, 202101],
            "drug_code": ["01234567", "01234568", "09999001", "08888001"],
            "drug_name": ["プレドニゾロン", "オンダンセトロン", "アモキシシリン", "アムロジピン"],
            "atc_code": ["H02AB", "A04AA", "J01CA04", "C08CA01"],
            "days_supply": [5, 3, 7, 30],
            "quantity": [10, 6, 14, 30],
            "drug_cost": [100, 80, 120, 200],
            "source_claim_id": ["C1", "C2", "C3", "C5"],
        }
    )


@pytest.fixture
def fake_procedures() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["P001", "P001", "P003"],
            "event_month": [202003, 202008, 202101],
            "procedure_code": ["160180410", "190178210", "140000000"],
            "procedure_name": ["小児食物アレルギー負荷検査", "負荷検査", "透析"],
            "points": [500, 500, 1000],
            "quantity": [1, 1, 1],
            "source_claim_id": ["C1", "C1", "C5"],
        }
    )


@pytest.fixture
def minimal_defs():
    return {
        "diagnosis_groups": {
            "fpies_name": {
                "logic": "OR",
                "rules": [
                    {"code_column": "diagnosis_code", "codes": ["8848201"], "match": "exact"},
                    {"code_column": "diagnosis_name", "codes": ["FPIES"], "match": "contains"},
                ],
                "exclude_suspected": True,
                "output": {"incident": {"washout_months": 6}},
            },
            "diabetes": {
                "code_column": "icd10_code",
                "codes": ["E11"],
                "match": "prefix",
                "exclude_suspected": True,
                "output": {"incident": {"washout_months": 6}},
            },
            "hypertension": {
                "code_column": "icd10_code",
                "codes": ["I10"],
                "match": "prefix",
            },
        },
        "medication_groups": {
            "steroid": {
                "code_column": "drug_name",
                "codes": ["プレド"],
                "match": "contains",
                "output": {"incident": {"washout_months": 6}},
            },
            "antibiotic": {
                "code_column": "atc_code",
                "codes": ["J01"],
                "match": "prefix",
                "output": {"incident": {"washout_months": 6}},
            },
        },
        "procedure_groups": {
            "ofc": {
                "code_column": "procedure_code",
                "codes": ["160180410", "190178210"],
                "match": "exact",
            },
            "dialysis": {
                "code_column": "procedure_code",
                "codes": ["140000000"],
                "match": "exact",
            },
        },
        "cooccurrence_groups": {
            "fpies_ofc_same_month": {
                "time_scope": "same_month",
                "components": [
                    {"table": "condition_event", "group": "fpies_name"},
                    {"table": "procedure_event", "group": "ofc"},
                ],
                "output": {"incident": {"washout_months": 6}},
            }
        },
        "composite_features": {
            "acute_proxy": {
                "logic": "OR",
                "components": ["med_steroid_flag_obs"],
            },
            "multi_dx": {
                "logic": "threshold",
                "threshold": 2,
                "components": ["dx_diabetes_flag_obs", "dx_hypertension_flag_obs"],
            },
        },
        "exclusive_groups": {
            "pathway_group": {
                "default": "other",
                "rules": [
                    {"label": "fpies_ofc", "condition": "combo_fpies_ofc_same_month_flag_obs == 1"},
                    {"label": "diabetes_only", "condition": "dx_diabetes_flag_obs == 1"},
                ],
            }
        },
        "comorbidity_groups": {
            "diabetes_cm": {
                "code_column": "icd10_code",
                "codes": ["E11"],
                "match": "prefix",
                "weight": 1,
            }
        },
    }
