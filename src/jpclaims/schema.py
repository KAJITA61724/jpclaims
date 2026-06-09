"""Standard event model schemas."""

from __future__ import annotations

from typing import Any

PERSON_COLUMNS = [
    "person_id",
    "sex",
    "birth_ym",
    "birth_year",
    "observation_start_ym",
    "observation_end_ym",
    "death_flag",
    "insurance_type",
    "family_id",
    "relationship",
    "self_family",
]

CLAIM_COLUMNS = [
    "claim_id",
    "person_id",
    "claim_month",
    "claim_type",
    "setting",
    "facility_id",
    "department",
    "total_points",
    "total_visit_days",
]

CONDITION_EVENT_COLUMNS = [
    "person_id",
    "event_month",
    "diagnosis_code",
    "diagnosis_name",
    "icd10_code",
    "suspected_flag",
    "primary_flag",
    "source_claim_id",
]

DRUG_EVENT_COLUMNS = [
    "person_id",
    "event_month",
    "drug_code",
    "yj_code",
    "price_code",
    "atc_code",
    "drug_name",
    "ingredient",
    "drug_class",
    "days_supply",
    "quantity",
    "drug_cost",
    "source_claim_id",
]

PROCEDURE_EVENT_COLUMNS = [
    "person_id",
    "event_month",
    "procedure_code",
    "procedure_name",
    "procedure_group",
    "points",
    "quantity",
    "source_claim_id",
]

VISIT_EVENT_COLUMNS = [
    "person_id",
    "event_month",
    "setting",
    "inpatient_flag",
    "outpatient_flag",
    "dispensing_flag",
    "facility_id",
    "department",
    "source_claim_id",
]

CHECKUP_EVENT_COLUMNS = [
    "person_id",
    "checkup_month",
    "bmi",
    "waist",
    "sbp",
    "dbp",
    "hba1c",
    "fpg",
    "ldl",
    "hdl",
    "tg",
    "ast",
    "alt",
    "ggtp",
    "egfr",
    "smoking_flag",
    "drinking_flag",
    "exercise_flag",
]

JP_GENERIC_COLUMN_MAP: dict[str, dict[str, str]] = {
    "person": {
        "加入者id": "person_id",
        "加入者性別": "sex",
        "性別": "sex",
        "加入者生年月": "birth_ym",
        "生年月": "birth_ym",
        "観察開始年月": "observation_start_ym",
        "観察終了年月": "observation_end_ym",
        "観察終了理由(死亡)フラグ": "death_flag",
        "死亡フラグ": "death_flag",
        "保険種別": "insurance_type",
        "家族id": "family_id",
        "続柄": "relationship",
        "本人家族": "self_family",
    },
    "claim": {
        "加入者id": "person_id",
        "レセid": "claim_id",
        "レセ種別": "claim_type",
        "診療年月": "claim_month",
        "医療施設id": "facility_id",
        "レセプト診療科": "department",
        "診療実日数": "total_visit_days",
        "総点数": "total_points",
    },
    "condition_event": {
        "加入者id": "person_id",
        "診療年月": "event_month",
        "標準傷病コード": "diagnosis_code",
        "標準病名": "diagnosis_name",
        "icd10_code": "icd10_code",
        "icd10小分類": "icd10_code",
        "疑いフラグ": "suspected_flag",
        "主傷病フラグ": "primary_flag",
        "レセid": "source_claim_id",
    },
    "drug_event": {
        "加入者id": "person_id",
        "診療年月": "event_month",
        "医薬品コード": "drug_code",
        "医薬品名": "drug_name",
        "atc_code": "atc_code",
        "who-atcコード": "atc_code",
        "1処方あたりの投与日数": "days_supply",
        "投薬量": "quantity",
        "総点数": "drug_cost",
        "レセid": "source_claim_id",
    },
    "procedure_event": {
        "加入者id": "person_id",
        "診療年月": "event_month",
        "標準化診療行為コード": "procedure_code",
        "標準化診療行為名": "procedure_name",
        "レセプト記載点数": "points",
        "数量": "quantity",
        "レセid": "source_claim_id",
    },
    "checkup_event": {
        "加入者id": "person_id",
        "健診実施年月日": "checkup_date_raw",
        "bmi": "bmi",
        "腹囲": "waist",
        "収縮期血圧": "sbp",
        "拡張期血圧": "dbp",
        "hba1c": "hba1c",
        "空腹時血糖": "fpg",
        "ldlコレステロール": "ldl",
        "hdlコレステロール": "hdl",
        "中性脂肪(トリグリセリド)": "tg",
        "got(ast)": "ast",
        "gpt(alt)": "alt",
        "γ-gt(γ-gtp)": "ggtp",
    },
}

TABLE_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "person": ["person_id", "observation_start_ym", "observation_end_ym"],
    "claim": ["person_id", "claim_id", "claim_month"],
    "condition_event": ["person_id", "event_month"],
    "drug_event": ["person_id", "event_month"],
    "procedure_event": ["person_id", "event_month"],
    "visit_event": ["person_id", "event_month"],
    "checkup_event": ["person_id"],
}

STRING_CODE_COLUMNS: dict[str, list[str]] = {
    "condition_event": ["diagnosis_code", "icd10_code"],
    "drug_event": ["drug_code", "yj_code", "price_code", "atc_code"],
    "procedure_event": ["procedure_code"],
    "claim": ["claim_id"],
    "person": ["person_id", "family_id"],
}


def get_schema(schema_name: str = "jp_generic") -> dict[str, Any]:
    if schema_name != "jp_generic":
        raise ValueError(f"Unknown schema: {schema_name}")
    return {
        "column_map": JP_GENERIC_COLUMN_MAP,
        "required": TABLE_REQUIRED_COLUMNS,
        "string_codes": STRING_CODE_COLUMNS,
    }
