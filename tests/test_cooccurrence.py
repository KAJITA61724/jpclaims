from jpclaims.datamart import build_patient_datamart


def test_cooccurrence(fake_person, fake_conditions, fake_procedures, minimal_defs):
    events = {
        "condition_event": fake_conditions,
        "drug_event": None,
        "procedure_event": fake_procedures,
    }
    from jpclaims.features.cooccurrence import build_cooccurrence_features

    out = build_cooccurrence_features(
        fake_person, events, minimal_defs["cooccurrence_groups"], minimal_defs
    )
    p1 = out.loc[out.person_id == "P001"].iloc[0]
    assert p1["combo_fpies_ofc_same_month_flag_obs"] == 1
    assert p1["combo_fpies_ofc_same_month_incident_6m_flag"] == 0
