from jpclaims.features.composite import assign_exclusive_group, build_composite_features


def test_composite_and_exclusive(fake_person, fake_conditions, fake_drugs, minimal_defs):
    from jpclaims.datamart import build_patient_datamart

    dm, _ = build_patient_datamart(
        person=fake_person,
        condition_event=fake_conditions,
        drug_event=fake_drugs,
        code_definitions=minimal_defs,
        return_report=True,
    )
    assert "acute_proxy" in dm.columns
    assert dm["acute_proxy"].max() == 1
    assert set(dm["pathway_group"].unique()).issubset({"fpies_ofc", "diabetes_only", "other"})
