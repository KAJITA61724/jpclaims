from jpclaims.features.procedures import build_procedure_features


def test_procedure_features(fake_person, fake_procedures, minimal_defs):
    out = build_procedure_features(
        fake_person, fake_procedures, minimal_defs["procedure_groups"]
    )
    p1 = out.loc[out.person_id == "P001"].iloc[0]
    assert p1["proc_ofc_flag_obs"] == 1
    assert p1["proc_ofc_count_obs"] == 2
    assert p1["proc_dialysis_total_points_obs"] == 0
