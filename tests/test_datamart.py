from jpclaims.datamart import build_patient_datamart
from jpclaims.features.monthly_panel import build_monthly_panel


def test_datamart_retention(fake_person, fake_claims, fake_conditions, fake_drugs, fake_procedures, minimal_defs):
    dm, report = build_patient_datamart(
        person=fake_person,
        claim=fake_claims,
        condition_event=fake_conditions,
        drug_event=fake_drugs,
        procedure_event=fake_procedures,
        code_definitions=minimal_defs,
        return_report=True,
    )
    assert len(dm) == len(fake_person)
    assert dm["person_id"].duplicated().sum() == 0
    assert report["patient_retention_check"] == 1.0
    flag_cols = [c for c in dm.columns if c.endswith("_flag_obs")]
    for col in flag_cols:
        assert set(dm[col].dropna().unique()).issubset({0, 1})


def test_monthly_panel(fake_person, fake_claims, fake_conditions, minimal_defs):
    panel = build_monthly_panel(
        person=fake_person,
        claim=fake_claims,
        condition_event=fake_conditions,
        code_definitions=minimal_defs,
    )
    assert {"person_id", "month", "monthly_visit_flag"}.issubset(panel.columns)
    assert panel["monthly_visit_flag"].dtype.kind in "iu"
