import pandas as pd

from jpclaims.code_match import apply_group_definition


def test_exact_prefix_contains_regex():
    df = pd.DataFrame(
        {
            "icd10_code": ["E110", "I10", "J45"],
            "diagnosis_name": ["糖尿病", "高血圧", "FPIES疑い"],
        }
    )
    assert apply_group_definition(df, {"code_column": "icd10_code", "codes": ["E11"], "match": "prefix"}).tolist() == [
        True,
        False,
        False,
    ]
    assert apply_group_definition(
        df, {"code_column": "diagnosis_name", "codes": ["FPIES"], "match": "contains"}
    ).tolist() == [False, False, True]
    assert apply_group_definition(
        df, {"code_column": "diagnosis_name", "codes": ["^FPIES"], "match": "regex"}
    ).tolist() == [False, False, True]


def test_and_or_logic():
    df = pd.DataFrame({"a": ["X", "Y"], "b": ["P", "X"]})
    and_def = {
        "logic": "AND",
        "rules": [
            {"code_column": "a", "codes": ["X"], "match": "exact"},
            {"code_column": "b", "codes": ["P"], "match": "exact"},
        ],
    }
    or_def = {
        "logic": "OR",
        "rules": [
            {"code_column": "a", "codes": ["Y"], "match": "exact"},
            {"code_column": "b", "codes": ["P"], "match": "exact"},
        ],
    }
    assert apply_group_definition(df, and_def).tolist() == [True, False]
    assert apply_group_definition(df, or_def).tolist() == [True, True]
