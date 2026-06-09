from jpclaims.features.diagnoses import build_diagnosis_features


def test_diagnosis_features(fake_person, fake_conditions, minimal_defs):
    out = build_diagnosis_features(
        fake_person, fake_conditions, minimal_defs["diagnosis_groups"]
    )
    p1 = out.loc[out.person_id == "P001"].iloc[0]
    assert p1["dx_fpies_name_flag_obs"] == 1
    assert p1["dx_fpies_name_month_count_obs"] == 2
    assert p1["dx_fpies_name_incident_6m_flag"] == 0
    p2 = out.loc[out.person_id == "P002"].iloc[0]
    assert p2["dx_diabetes_flag_obs"] == 0
    assert p2["dx_hypertension_suspected_count"] >= 0
