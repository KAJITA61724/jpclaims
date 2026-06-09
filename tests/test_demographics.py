from jpclaims.features.demographics import build_demographic_features


def test_demographics(fake_person):
    out = build_demographic_features(fake_person)
    assert len(out) == 3
    assert "age" in out.columns
    assert out.loc[out.person_id == "P001", "sex"].iloc[0] == 1
