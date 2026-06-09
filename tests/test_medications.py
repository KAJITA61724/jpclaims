from jpclaims.features.medications import build_medication_features


def test_medication_features(fake_person, fake_drugs, minimal_defs):
    out = build_medication_features(fake_person, fake_drugs, minimal_defs["medication_groups"])
    p1 = out.loc[out.person_id == "P001"].iloc[0]
    assert p1["med_steroid_flag_obs"] == 1
    assert p1["med_steroid_total_days_obs"] == 5
    assert p1["med_steroid_new_user_flag"] == 0
