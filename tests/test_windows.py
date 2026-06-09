from jpclaims.windows import compute_window_availability, define_observation_window


def test_window_availability(fake_person):
    out = compute_window_availability(fake_person)
    assert "baseline_12m_available_flag" in out.columns
    obs = define_observation_window(fake_person)
    assert int(obs.loc[obs.person_id == "P001", "observed_months"].iloc[0]) >= 12
